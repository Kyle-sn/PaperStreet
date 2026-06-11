"""
config.py

The single declarative specification of a backtest.

A `BacktestConfig` fully describes a run: which strategy, which symbol, which
data window, and which cost/fill assumptions. Everything downstream (data
loading, simulated broker, portfolio, metrics) is driven off this object, so
swapping a strategy, symbol, or cost model is a config change — never an engine
edit. This mirrors the strategy layer's config-driven selection (build_strategy
by name + params) so the two halves feel the same.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Fill models. "next_open" fills a bar-N signal at bar N+1's open and is the
# only model that avoids lookahead bias (see docs/BACKTESTING.md). "close" fills
# at the signalling bar's own close — convenient but optimistic/unrealistic; it
# exists only for quick sanity comparisons, never for trusted results.
FILL_MODELS = ("next_open", "close")

# Where bar data comes from. "db" reads only the local market_data_bars cache,
# "ibkr" always fetches from TWS, "auto" reads the cache and fetches+caches on a
# miss (the fast default — connect once to populate, then iterate offline).
DATA_SOURCES = ("auto", "db", "ibkr")


@dataclass
class BacktestConfig:
    """
    Declarative spec for a single backtest run.

    Required
    --------
    strategy_name : str
        Registered strategy name (the key passed to build_strategy).
    symbol : str
        Symbol to trade. One backtest, one symbol — matches the strategy layer's
        one-instance-one-symbol rule.

    Strategy
    --------
    strategy_params : dict
        Constructor kwargs forwarded to the strategy (e.g. window, order_size).

    Data window
    -----------
    bar_size : str
        IBKR bar size ("1 day", "5 mins", ...). Selects which cached series to
        read and how returns are annualized.
    start, end : str | None
        Inclusive ISO date/datetime bounds (e.g. "2024-01-01"). None means no
        bound on that side — use the full available history.
    data_source : str
        One of DATA_SOURCES. Defaults to "auto".
    duration : str
        IBKR duration string used only when data must be fetched from TWS
        (data_source "ibkr", or "auto" on a cache miss). Ignored when reading
        from the cache.

    Capital and costs
    -----------------
    starting_cash : float
        Initial portfolio cash.
    commission_per_share : float
        Per-share commission, applied to every fill.
    commission_min : float
        Minimum commission per fill (IBKR-style $1.00 floor).
    slippage_bps : float
        Slippage applied to each fill, in basis points of fill price. Models the
        half-spread you cross; buys fill higher, sells fill lower.

    Execution model
    ---------------
    fill : str
        One of FILL_MODELS. Defaults to "next_open".
    allow_short : bool
        If False, SELLs are capped at the current long position (the old
        long-only behavior). If True, the portfolio may go net short.
    """

    strategy_name: str
    symbol: str
    strategy_params: dict = field(default_factory=dict)

    bar_size: str = "1 day"
    start: str | None = None
    end: str | None = None
    data_source: str = "auto"
    duration: str = "5 Y"

    starting_cash: float = 100_000.0
    commission_per_share: float = 0.005
    commission_min: float = 1.0
    slippage_bps: float = 0.0

    fill: str = "next_open"
    allow_short: bool = True

    def __post_init__(self) -> None:
        if self.fill not in FILL_MODELS:
            raise ValueError(f"fill must be one of {FILL_MODELS}, got {self.fill!r}")
        if self.data_source not in DATA_SOURCES:
            raise ValueError(f"data_source must be one of {DATA_SOURCES}, got {self.data_source!r}")
        if self.starting_cash <= 0:
            raise ValueError(f"starting_cash must be positive, got {self.starting_cash}")
