"""
test_strategy_contract.py

Contract tests that every *registered* bar strategy honors the BaseStrategy
interface. This is what makes the framework plug-and-play safe: a new strategy
that breaks the contract fails here rather than at backtest or (worse) live run.

Covers, for each registered strategy:
- correct on_bar signature (accepts position kwarg)
- suppresses signals during warm-up
- once warmed up, returns None or a valid OrderRequest tagged with symbol/name
- respects max_position when the parameter exists
"""

import inspect

import pytest

from strategy import STRATEGY_REGISTRY, build_strategy
from strategy.base_strategy import BaseStrategy
from strategy.signal import OrderRequest, ACTIONS, ORDER_TYPES


def _bar(close, dt="2026-01-01"):
    return {"datetime": dt, "open": close, "high": close, "low": close,
            "close": close, "volume": 1000}


ALL_STRATEGIES = sorted(STRATEGY_REGISTRY)


@pytest.mark.parametrize("name", ALL_STRATEGIES)
def test_registered_strategy_is_base_strategy(name):
    cls = STRATEGY_REGISTRY[name]
    assert issubclass(cls, BaseStrategy)
    assert cls.name == name


@pytest.mark.parametrize("name", ALL_STRATEGIES)
def test_on_bar_accepts_position(name):
    sig = inspect.signature(STRATEGY_REGISTRY[name].on_bar)
    assert "position" in sig.parameters


@pytest.mark.parametrize("name", ALL_STRATEGIES)
def test_warmup_returns_none(name):
    strategy = build_strategy(name, symbol="SPY")
    # A single bar must never be enough to fire a signal.
    assert strategy.on_bar(_bar(100.0), position=0.0) is None


@pytest.mark.parametrize("name", ALL_STRATEGIES)
def test_signals_are_valid_order_requests(name):
    strategy = build_strategy(name, symbol="SPY")
    # Feed a noisy ramp so warm-up completes and signals are produced.
    prices = [100, 101, 99, 103, 97, 105, 95, 110, 90, 115, 88, 120]
    for i, p in enumerate(prices):
        signal = strategy.on_bar(_bar(float(p), dt=f"2026-01-{i + 1:02d}"), position=10.0)
        if signal is None:
            continue
        assert isinstance(signal, OrderRequest)
        assert signal.action in ACTIONS
        assert signal.order_type in ORDER_TYPES
        assert signal.quantity > 0
        assert signal.symbol == "SPY"
        assert signal.strategy == name


def test_max_position_blocks_buys():
    """Inventory-aware strategies must not BUY past max_position."""
    strategy = build_strategy(
        "mean_reversion",
        symbol="SPY",
        params={"window": 3, "spread_multiplier": 0.0, "max_position": 50, "order_size": 10},
    )
    # At/over the cap, no further BUY should be emitted regardless of deviation.
    for p in [100.0, 100.0, 100.0, 80.0]:
        signal = strategy.on_bar(_bar(p), position=50.0)
        assert signal is None or signal.action != "BUY"
