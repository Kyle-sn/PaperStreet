"""
broker.py

Simulated broker — the fill model the old harness lacked.

It turns an OrderRequest into a Fill under explicit, conservative assumptions,
and (critically) it is the piece that prevents lookahead bias: under the
"next_open" model a signal computed from bar N's close is filled at bar N+1's
open, never at bar N's own close.

Fill assumptions (see docs/BACKTESTING.md):
  - Market orders fill at the reference price (next bar open, or this bar close
    under the "close" model), then pay `slippage_bps` of that price — buys fill
    higher, sells fill lower.
  - Limit orders fill only if the bar trades through the limit (buy: low <=
    limit; sell: high >= limit), at the better of the limit and the reference
    price. Limit fills pay no slippage — you get your price or better.
  - Orders are good-for-one-bar: a limit that does not cross is dropped, not
    carried forward. No partial fills, no queue position.
"""

from __future__ import annotations

from dataclasses import dataclass

from strategy.signal import OrderRequest


@dataclass
class Fill:
    """A simulated execution produced by SimBroker."""

    datetime: object
    action: str          # 'BUY' or 'SELL'
    quantity: float
    price: float          # all-in fill price (includes slippage for market orders)
    commission: float


class SimBroker:
    """
    Simulated broker applying fill, slippage, and commission assumptions.

    The engine queues a signal with `queue()` after each bar and, on the next
    bar, calls `fill_pending()` (next_open model) — or, under the "close" model,
    calls `fill_now()` with the just-generated signal against the same bar.
    """

    def __init__(self, commission_per_share: float = 0.005, commission_min: float = 1.0,
                 slippage_bps: float = 0.0):
        self.commission_per_share = commission_per_share
        self.commission_min = commission_min
        self.slippage_bps = slippage_bps
        self._pending: OrderRequest | None = None

    # ------------------------------------------------------------------
    # next_open model
    # ------------------------------------------------------------------

    def queue(self, order: OrderRequest | None) -> None:
        """Hold an order to be filled against the next bar. Overwrites any
        unfilled prior order (good-for-one-bar)."""
        self._pending = order

    def fill_pending(self, bar: dict) -> Fill | None:
        """Attempt to fill the queued order against `bar`, using its open as the
        market reference. Clears the pending order regardless of outcome."""
        order = self._pending
        self._pending = None
        if order is None:
            return None
        return self._simulate(order, bar, market_price=bar["open"])

    # ------------------------------------------------------------------
    # close model
    # ------------------------------------------------------------------

    def fill_now(self, order: OrderRequest | None, bar: dict) -> Fill | None:
        """Fill an order against the same bar, using its close as the market
        reference. Optimistic — for quick comparisons only."""
        if order is None:
            return None
        return self._simulate(order, bar, market_price=bar["close"])

    # ------------------------------------------------------------------
    # Shared fill simulation
    # ------------------------------------------------------------------

    def _simulate(self, order: OrderRequest, bar: dict, market_price: float) -> Fill | None:
        price = self._fill_price(order, bar, market_price)
        if price is None:
            return None
        commission = max(self.commission_min, self.commission_per_share * order.quantity)
        return Fill(
            datetime=bar.get("datetime"),
            action=order.action,
            quantity=order.quantity,
            price=price,
            commission=commission,
        )

    def _fill_price(self, order: OrderRequest, bar: dict, market_price: float) -> float | None:
        slip = self.slippage_bps / 10_000.0

        if order.order_type == "MKT":
            if order.action == "BUY":
                return market_price * (1 + slip)
            return market_price * (1 - slip)

        # LMT — fill only if the bar trades through the limit; take the better of
        # the limit and the reference price (handles a gap past the limit).
        limit = order.limit_price
        if order.action == "BUY":
            if bar["low"] <= limit:
                return min(limit, market_price)
            return None
        if bar["high"] >= limit:
            return max(limit, market_price)
        return None
