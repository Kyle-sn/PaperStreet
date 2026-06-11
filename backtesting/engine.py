"""
engine.py

The backtest replay loop. It wires the pieces together but owns no policy of its
own: data comes pre-loaded, fills come from SimBroker, accounting from
Portfolio, and signals from the strategy.

The loop structure is what enforces the no-lookahead rule under the "next_open"
model: each bar first fills the order queued on the *previous* bar (at this
bar's open), and only then asks the strategy for a new signal off this bar's
close. The strategy can therefore never trade on information from the same bar
that produced the signal.
"""

from __future__ import annotations

import pandas as pd

from backtesting.broker import SimBroker
from backtesting.portfolio import Portfolio
from strategy.base_strategy import BaseStrategy


class BacktestEngine:
    """
    Replays bars through a strategy, broker, and portfolio.

    Parameters
    ----------
    data : pd.DataFrame
        Bars with a `datetime` column plus OHLCV, sorted oldest-first.
    strategy : BaseStrategy
        Configured strategy instance (symbol already set).
    portfolio : Portfolio
    broker : SimBroker
    fill : str
        "next_open" (fills the prior bar's signal at this bar's open) or "close"
        (fills this bar's signal at its own close). See config.FILL_MODELS.
    """

    def __init__(self, data: pd.DataFrame, strategy: BaseStrategy,
                 portfolio: Portfolio, broker: SimBroker, fill: str = "next_open"):
        self.data = data
        self.strategy = strategy
        self.portfolio = portfolio
        self.broker = broker
        self.fill = fill

    def run(self) -> tuple[list[float], list]:
        """
        Execute the backtest.

        Returns
        -------
        (equity, timestamps)
            equity : list[float] — mark-to-market value at each bar close.
            timestamps : list — the `datetime` of each bar, aligned to equity.
        """
        equity: list[float] = []
        timestamps: list = []

        for bar in self.data.to_dict("records"):
            if self.fill == "next_open":
                # Fill the order queued on the previous bar before generating a
                # new one — this is the lookahead barrier.
                fill = self.broker.fill_pending(bar)
                self._apply(fill)
                signal = self.strategy.on_bar(bar, position=self.portfolio.position)
                self.broker.queue(signal)
            else:  # close
                signal = self.strategy.on_bar(bar, position=self.portfolio.position)
                fill = self.broker.fill_now(signal, bar)
                self._apply(fill)

            equity.append(self.portfolio.mark(bar["close"]))
            timestamps.append(bar["datetime"])

        return equity, timestamps

    def _apply(self, fill) -> None:
        if fill is None:
            return
        self.portfolio.apply(fill)
        self.strategy.on_fill(fill.action, fill.quantity, fill.price)
