"""
portfolio.py

Simulated portfolio accounting for backtests.

Tracks cash, net position (long *or* short — the old version was long-only and
silently dropped the sell side of symmetric strategies), weighted-average cost,
and realized PnL. It consumes Fills from SimBroker; it does not decide fills.

Position is the authoritative source the engine feeds back into
strategy.on_bar(bar, position), mirroring how live trading injects the
broker-confirmed position — so a strategy sees the same information set in both.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Trade:
    """One executed fill, with the realized PnL it produced (0 for trades that
    only open/add to a position; non-zero when they reduce/close one)."""

    datetime: object
    action: str
    quantity: float
    price: float
    commission: float
    realized: float


class Portfolio:
    """
    Cash + position accounting with long/short support.

    Attributes
    ----------
    cash : float
        Available cash. A buy reduces it, a sell increases it; commissions are
        deducted on every fill.
    position : float
        Net shares. Positive long, negative short, 0 flat.
    avg_cost : float
        Weighted-average entry price of the open position (0 when flat).
    realized_pnl : float
        Cumulative PnL from closing/reducing positions (excludes commission).
    commission_total : float
        Cumulative commission paid.
    trades : list[Trade]
        Every applied fill, in order.
    """

    def __init__(self, starting_cash: float = 100_000.0, allow_short: bool = True):
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.position = 0.0
        self.avg_cost = 0.0
        self.realized_pnl = 0.0
        self.commission_total = 0.0
        self.allow_short = allow_short
        self.trades: list[Trade] = []

    def apply(self, fill) -> None:
        """Apply a Fill, updating cash, position, average cost, and realized PnL."""
        signed = fill.quantity if fill.action == "BUY" else -fill.quantity

        # Long-only guard: cap a sell at the current long position so we never go
        # net short when shorting is disabled. A fully-suppressed sell is a no-op.
        if not self.allow_short and signed < 0:
            signed = max(signed, -self.position)
            if signed == 0:
                return

        price = fill.price
        new_position = self.position + signed

        realized = 0.0
        # Reducing exposure: position and the trade point opposite ways.
        if self.position != 0 and (self.position > 0) != (signed > 0):
            closing = min(abs(signed), abs(self.position))
            direction = 1 if self.position > 0 else -1
            realized = (price - self.avg_cost) * closing * direction
            self.realized_pnl += realized

        # Update weighted-average cost.
        if new_position == 0:
            self.avg_cost = 0.0
        elif (self.position >= 0) == (new_position >= 0) and abs(new_position) > abs(self.position):
            # Increasing same-side exposure (including opening from flat).
            self.avg_cost = (
                self.avg_cost * abs(self.position) + price * abs(signed)
            ) / abs(new_position)
        elif (self.position > 0) != (new_position > 0):
            # Crossed through zero: the residual is a fresh position at this price.
            self.avg_cost = price
        # else: reducing same-side exposure — avg_cost is unchanged.

        self.cash -= price * signed
        self.cash -= fill.commission
        self.commission_total += fill.commission
        self.position = new_position

        self.trades.append(Trade(
            datetime=fill.datetime, action=fill.action, quantity=abs(signed),
            price=price, commission=fill.commission, realized=realized,
        ))

    def mark(self, price: float) -> float:
        """Mark-to-market equity: cash + position valued at `price`."""
        return self.cash + self.position * price
