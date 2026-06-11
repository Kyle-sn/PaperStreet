"""
backtesting/

Plug-and-play backtesting for bar strategies. Describe a run with a
`BacktestConfig` and call `run_backtest(config)` — it loads bars (cache-first),
builds the strategy by name from the registry, replays it through a simulated
broker and portfolio, and returns a `BacktestResult` with metrics.

    from backtesting import BacktestConfig, run_backtest

    result = run_backtest(BacktestConfig(
        strategy_name="mean_reversion", symbol="SPY",
        strategy_params={"window": 20},
    ))
    print(result.summary())
"""

from backtesting.config import BacktestConfig
from backtesting.result import BacktestResult
from backtesting.runner import run_backtest

__all__ = ["BacktestConfig", "BacktestResult", "run_backtest"]
