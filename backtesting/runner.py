"""
runner.py

The one-call programmatic API: `run_backtest(config) -> BacktestResult`.

This is the plug-and-play entry point — give it a BacktestConfig and it loads
data, builds the strategy by name from the registry (same factory the live loop
uses), runs the replay, and returns a result with metrics. Notebooks and scripts
call this directly; run_backtest.py is just a thin CLI wrapper around it.
"""

from __future__ import annotations

from backtesting.broker import SimBroker
from backtesting.config import BacktestConfig
from backtesting.data import load_bars
from backtesting.engine import BacktestEngine
from backtesting.metrics import compute_metrics
from backtesting.portfolio import Portfolio
from backtesting.result import BacktestResult
from strategy.registry import build_strategy


def run_backtest(config: BacktestConfig) -> BacktestResult:
    """Run a single backtest end-to-end and return its result."""
    bars = load_bars(config)

    strategy = build_strategy(config.strategy_name, symbol=config.symbol,
                              params=config.strategy_params)
    portfolio = Portfolio(starting_cash=config.starting_cash, allow_short=config.allow_short)
    broker = SimBroker(
        commission_per_share=config.commission_per_share,
        commission_min=config.commission_min,
        slippage_bps=config.slippage_bps,
    )
    engine = BacktestEngine(bars, strategy, portfolio, broker, fill=config.fill)

    strategy.on_start()
    try:
        equity, timestamps = engine.run()
    finally:
        strategy.on_stop()

    metrics = compute_metrics(equity, portfolio.trades, config.bar_size)
    return BacktestResult(
        config=config,
        equity=equity,
        timestamps=timestamps,
        trades=portfolio.trades,
        metrics=metrics,
    )
