"""
result.py

The object a backtest returns: the equity curve, the trade log, and the computed
metrics, plus convenience accessors for notebooks (DataFrames, a printable
summary). Keeping everything on one object means a research cell can do
`run_backtest(cfg).summary()` or pull `.equity_frame()` to plot.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from backtesting.config import BacktestConfig
from backtesting.metrics import Metrics


@dataclass
class BacktestResult:
    config: BacktestConfig
    equity: list[float]
    timestamps: list
    trades: list          # list[Trade]
    metrics: Metrics

    @property
    def final_equity(self) -> float:
        return self.equity[-1] if self.equity else self.config.starting_cash

    @property
    def pnl(self) -> float:
        return self.final_equity - self.config.starting_cash

    def equity_frame(self) -> pd.DataFrame:
        """Equity curve as a DataFrame indexed by bar datetime."""
        return pd.DataFrame({"equity": self.equity}, index=pd.Index(self.timestamps, name="datetime"))

    def trades_frame(self) -> pd.DataFrame:
        """Trade log as a DataFrame (empty frame if no trades)."""
        if not self.trades:
            return pd.DataFrame(columns=["datetime", "action", "quantity", "price",
                                         "commission", "realized"])
        return pd.DataFrame([t.__dict__ for t in self.trades])

    def summary(self) -> str:
        """A formatted, printable performance summary."""
        m = self.metrics
        c = self.config
        lines = [
            f"Backtest: {c.strategy_name} on {c.symbol} ({c.bar_size})",
            f"  Bars:               {len(self.equity)}",
            f"  Starting cash:      ${c.starting_cash:,.2f}",
            f"  Final equity:       ${self.final_equity:,.2f}",
            f"  PnL:                ${self.pnl:,.2f}",
            f"  Total return:       {m.total_return:>8.2%}",
            f"  Annualized return:  {m.annualized_return:>8.2%}",
            f"  Sharpe:             {m.sharpe:>8.2f}",
            f"  Max drawdown:       {m.max_drawdown:>8.2%}",
            f"  Win rate:           {m.win_rate:>8.2%}",
            f"  Avg win / loss:     {m.avg_win:>8.2f} / {m.avg_loss:.2f}",
            f"  Total trades:       {m.total_trades}",
            f"  Total commission:   ${m.total_commission:,.2f}",
        ]
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()
