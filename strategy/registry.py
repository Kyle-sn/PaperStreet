"""
registry.py

Name -> strategy-class registries plus a factory, so strategies can be selected
by string from config instead of by editing imports in run_live.py /
run_backtest.py. Swapping a strategy becomes a config change, not a code change.

Two families are kept separate because they consume different inputs and cannot
be used interchangeably:

  - bar strategies (BaseStrategy): consume OHLCV bars via on_bar
  - quoting strategies (BaseQuotingStrategy): consume settlement estimates via
    on_estimate (e.g. the ERCOT market maker)

Registration happens via decorator at class-definition time. strategy/__init__.py
imports every concrete strategy module so the registries are fully populated on
`import strategy`.
"""

from __future__ import annotations

from typing import Callable, TypeVar

STRATEGY_REGISTRY: dict[str, type] = {}
QUOTING_REGISTRY: dict[str, type] = {}

T = TypeVar("T", bound=type)


def _register(registry: dict[str, type], name: str | None) -> Callable[[T], T]:
    def decorator(cls: T) -> T:
        key = name or getattr(cls, "name", "")
        if not key:
            raise ValueError(f"{cls.__name__} must define a non-empty `name` to be registered")
        if key in registry and registry[key] is not cls:
            raise ValueError(f"Strategy name {key!r} is already registered to {registry[key].__name__}")
        cls.name = key
        registry[key] = cls
        return cls

    return decorator


def register_strategy(name: str | None = None) -> Callable[[T], T]:
    """Register a BaseStrategy subclass under `name` (defaults to the class's `name` attr)."""
    return _register(STRATEGY_REGISTRY, name)


def register_quoting_strategy(name: str | None = None) -> Callable[[T], T]:
    """Register a BaseQuotingStrategy subclass under `name`."""
    return _register(QUOTING_REGISTRY, name)


def build_strategy(name: str, symbol: str = "", params: dict | None = None):
    """
    Instantiate a registered bar strategy by name.

    Parameters
    ----------
    name : str
        Registered strategy name (the `name` class attribute).
    symbol : str
        Symbol this instance trades. One instance trades one symbol; run
        multiple instances to cover multiple symbols.
    params : dict, optional
        Constructor keyword arguments for the strategy.

    Returns
    -------
    BaseStrategy
        A configured strategy instance with `.symbol` set.
    """
    if name not in STRATEGY_REGISTRY:
        raise KeyError(f"Unknown strategy {name!r}. Registered: {sorted(STRATEGY_REGISTRY)}")
    strategy = STRATEGY_REGISTRY[name](**(params or {}))
    strategy.symbol = symbol
    return strategy


def build_quoting_strategy(name: str, params: dict | None = None):
    """Instantiate a registered quoting strategy by name."""
    if name not in QUOTING_REGISTRY:
        raise KeyError(f"Unknown quoting strategy {name!r}. Registered: {sorted(QUOTING_REGISTRY)}")
    return QUOTING_REGISTRY[name](**(params or {}))
