"""
metrics.py

Performance metrics computed from an equity curve and trade log — the summary
table docs/BACKTESTING.md specifies (the old harness printed only final value).

Annualization needs to know how many bars make up a year, which depends on bar
size. The map below uses 252 trading days/year and a 6.5-hour RTH session; it is
approximate (holidays, half-days) but consistent across runs.
"""

from __future__ import annotations

from dataclasses import dataclass

# Approximate number of RTH bars per year, by IBKR bar size.
_TRADING_DAYS = 252
_RTH_MINUTES = 390  # 6.5h regular session
_PERIODS_PER_YEAR = {
    "1 day": _TRADING_DAYS,
    "1 week": 52,
    "1 month": 12,
    "1 hour": _TRADING_DAYS * (_RTH_MINUTES / 60),
    "30 mins": _TRADING_DAYS * (_RTH_MINUTES / 30),
    "15 mins": _TRADING_DAYS * (_RTH_MINUTES / 15),
    "5 mins": _TRADING_DAYS * (_RTH_MINUTES / 5),
    "1 min": _TRADING_DAYS * _RTH_MINUTES,
}


@dataclass
class Metrics:
    total_return: float
    annualized_return: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    avg_win: float
    avg_loss: float
    total_trades: int
    total_commission: float


def periods_per_year(bar_size: str) -> float:
    return _PERIODS_PER_YEAR.get(bar_size, _TRADING_DAYS)


def compute_metrics(equity: list[float], trades: list, bar_size: str) -> Metrics:
    """
    Compute summary metrics.

    Parameters
    ----------
    equity : list[float]
        Mark-to-market equity at each bar close, oldest-first.
    trades : list[Trade]
        Applied fills (from Portfolio.trades). `realized` distinguishes closing
        trades (the round-trip outcomes used for win rate) from opening ones.
    bar_size : str
        IBKR bar size, used to annualize.
    """
    if len(equity) < 2:
        return Metrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, len(trades),
                       sum(t.commission for t in trades))

    ppy = periods_per_year(bar_size)
    total_return = equity[-1] / equity[0] - 1.0

    n = len(equity) - 1
    growth = equity[-1] / equity[0]
    annualized_return = growth ** (ppy / n) - 1.0 if growth > 0 else -1.0

    returns = [equity[i] / equity[i - 1] - 1.0 for i in range(1, len(equity))]
    sharpe = _sharpe(returns, ppy)
    max_drawdown = _max_drawdown(equity)

    # Win rate / avg win-loss are computed over trades that realized PnL (i.e.
    # closed or reduced a position); pure opening trades have realized == 0.
    closed = [t.realized for t in trades if t.realized != 0.0]
    wins = [r for r in closed if r > 0]
    losses = [r for r in closed if r < 0]
    win_rate = len(wins) / len(closed) if closed else 0.0
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0

    return Metrics(
        total_return=total_return,
        annualized_return=annualized_return,
        sharpe=sharpe,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        total_trades=len(trades),
        total_commission=sum(t.commission for t in trades),
    )


def _sharpe(returns: list[float], ppy: float) -> float:
    """Annualized Sharpe over cash (rf = 0). Returns 0.0 if volatility is zero."""
    n = len(returns)
    if n == 0:
        return 0.0
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / n
    std = var ** 0.5
    if std == 0:
        return 0.0
    return (mean / std) * (ppy ** 0.5)


def _max_drawdown(equity: list[float]) -> float:
    """Largest peak-to-trough decline as a negative fraction (0.0 if none)."""
    peak = equity[0]
    max_dd = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            max_dd = min(max_dd, v / peak - 1.0)
    return max_dd
