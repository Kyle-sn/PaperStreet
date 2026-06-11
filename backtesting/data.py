"""
data.py

Offline-first bar loader for backtests.

The big iteration win over the old harness: a backtest should not need a live
TWS connection on every run. Bars are read from the local SQLite cache
(market_data_bars); only on a cache miss does this connect to IBKR, fetch, and
write the bars back to the cache (IBKRMarketDataClient already upserts on fetch).
So you connect once to populate a symbol, then iterate offline indefinitely.

Returns a DataFrame with `datetime` as a *column* (not the index) plus OHLCV,
because the engine hands each row to the strategy as a dict that must carry a
"datetime" key (the strategy and DB layers otherwise keep datetime in the
index).
"""

from __future__ import annotations

import pandas as pd

from database import market_data as _mdb
from utils.log_config import setup_logger

from backtesting.config import BacktestConfig

logger = setup_logger(__name__)

_OHLCV = ["open", "high", "low", "close", "volume"]


def load_bars(config: BacktestConfig) -> pd.DataFrame:
    """
    Load bars for a backtest per its config's data_source and window.

    Returns
    -------
    pd.DataFrame
        Columns: datetime, open, high, low, close, volume. Sorted oldest-first.
        `datetime` is a column (tz-aware for intraday, date-typed for daily).

    Raises
    ------
    ValueError
        If no bars are available for the requested symbol/window.
    """
    if config.data_source == "ibkr":
        df = _fetch_from_ibkr(config)
    else:
        df = _read_from_cache(config)
        if df is None and config.data_source == "auto":
            logger.info(f"Cache miss for {config.symbol} ({config.bar_size}); fetching from IBKR")
            df = _fetch_from_ibkr(config)

    if df is None or df.empty:
        raise ValueError(
            f"No bars available for {config.symbol} (bar_size={config.bar_size}, "
            f"data_source={config.data_source}). Populate the cache first or use "
            f"data_source='ibkr'/'auto' with TWS running."
        )

    df = _apply_window(df, config.start, config.end)
    if df.empty:
        raise ValueError(
            f"No bars for {config.symbol} within window start={config.start} end={config.end}."
        )

    return df.reset_index(drop=True)


def _read_from_cache(config: BacktestConfig) -> pd.DataFrame | None:
    df = _mdb.get_bars(config.symbol, bar_size=config.bar_size)
    if df is None or df.empty:
        return None
    return _normalize(df)


def _fetch_from_ibkr(config: BacktestConfig) -> pd.DataFrame | None:
    # Imported lazily so the "db" path never pulls in the TWS/connection stack.
    from research.session import Session

    with Session() as session:
        df = session.market_data.get_bars(
            config.symbol, duration=config.duration, bar_size=config.bar_size
        )
    # get_bars already upserts the fetched bars into the cache as a side effect.
    return _normalize(df)


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Move a DatetimeIndex into a `datetime` column and keep only OHLCV."""
    df = df.copy()
    if "datetime" not in df.columns:
        df = df.reset_index().rename(columns={"index": "datetime"})
    cols = ["datetime"] + [c for c in _OHLCV if c in df.columns]
    return df[cols].sort_values("datetime").reset_index(drop=True)


def _apply_window(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    """Filter to [start, end] inclusive, matching the column's tz-awareness."""
    if start is not None:
        df = df[df["datetime"] >= _coerce_bound(start, df["datetime"])]
    if end is not None:
        df = df[df["datetime"] <= _coerce_bound(end, df["datetime"])]
    return df


def _coerce_bound(bound: str, col: pd.Series) -> pd.Timestamp:
    """Parse a bound to a Timestamp that compares cleanly against `col`.

    Intraday series are tz-aware; a naive bound would raise on comparison, so we
    localize it to the column's tz. Daily series are tz-naive and compare as-is.
    """
    ts = pd.Timestamp(bound)
    tz = getattr(col.dt, "tz", None)
    if tz is not None and ts.tzinfo is None:
        ts = ts.tz_localize(tz)
    return ts


if __name__ == "__main__":
    # Prefetch + cache a symbol so later backtests run fully offline.
    # Usage: python -m backtesting.data SYMBOL [bar_size] [duration]
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    bar_size = sys.argv[2] if len(sys.argv) > 2 else "1 day"
    duration = sys.argv[3] if len(sys.argv) > 3 else "5 Y"
    cfg = BacktestConfig(strategy_name="", symbol=symbol, bar_size=bar_size,
                         duration=duration, data_source="ibkr")
    bars = load_bars(cfg)
    print(f"Fetched and cached {len(bars)} {bar_size} bars for {symbol}")
    print(bars.head())
    print(bars.tail())
