"""
test_market_data.py

Integration tests for the market data layer. Requires TWS to be running.

What this covers
----------------
1. Session connects to TWS and disconnects cleanly
2. get_daily_bars returns a well-formed DataFrame
3. get_daily_bars respects the duration parameter
4. get_intraday_bars returns a well-formed DataFrame with timezone-aware index
5. get_bars works as a general-purpose passthrough
6. get_daily_bars_multi returns data for all requested symbols
7. get_close_prices returns an aligned multi-column DataFrame
8. A bad symbol fails gracefully without crashing the multi-symbol fetch

How to run
----------
    python test_market_data.py

Expected output: a PASS/FAIL summary for each test.
All tests require TWS to be running on port 7497.
"""

import traceback
import pandas as pd
from research.session import Session

# Symbols used across tests — liquid ETFs, should always have data
PRIMARY_SYMBOL = "SPY"
MULTI_SYMBOLS = ["SPY", "QQQ", "IWM"]
BAD_SYMBOL = "ZZZZINVALID"

EXPECTED_COLUMNS = {"open", "high", "low", "close", "volume"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_test(name: str, fn) -> bool:
    try:
        fn()
        print(f"  PASS  {name}")
        return True
    except AssertionError as e:
        print(f"  FAIL  {name}")
        print(f"        AssertionError: {e}")
        return False
    except Exception:
        print(f"  FAIL  {name}")
        traceback.print_exc()
        return False


def assert_valid_ohlcv(df: pd.DataFrame, label: str):
    """Shared assertions that apply to every bar DataFrame."""
    assert isinstance(df, pd.DataFrame), f"{label}: expected DataFrame, got {type(df)}"
    assert not df.empty, f"{label}: DataFrame is empty"
    assert EXPECTED_COLUMNS.issubset(df.columns), (
        f"{label}: missing columns. Expected {EXPECTED_COLUMNS}, got {set(df.columns)}"
    )
    assert df.index.is_monotonic_increasing, f"{label}: index is not sorted oldest-first"
    assert not df.index.duplicated().any(), f"{label}: index contains duplicate entries"
    assert df["close"].notna().all(), f"{label}: close column contains NaN values"


# ---------------------------------------------------------------------------
# Tests — one Session per test to keep them independent
# ---------------------------------------------------------------------------

def test_session_connects():
    """Session connects to TWS and is_connected returns True."""
    session = Session()
    assert session.is_connected, "Session.is_connected should be True after construction"
    assert session.market_data is not None, "Session.market_data should not be None"
    session.disconnect()
    assert not session.is_connected, "Session.is_connected should be False after disconnect"


def test_session_context_manager():
    """Context manager form connects and disconnects automatically."""
    with Session() as session:
        assert session.is_connected
    assert not session.is_connected


def test_get_daily_bars_default():
    """get_daily_bars with default duration returns valid daily OHLCV data."""
    with Session() as session:
        df = session.market_data.get_daily_bars(PRIMARY_SYMBOL)

    assert_valid_ohlcv(df, "get_daily_bars default")

    # Daily index should be date-like (no time component)
    assert hasattr(df.index, "date") or pd.api.types.is_datetime64_any_dtype(df.index), \
        "Daily bars should have a datetime index"

    # 1 month of daily bars should be roughly 18-23 trading days
    assert 15 <= len(df) <= 25, (
        f"Expected ~20 daily bars for 1 month, got {len(df)}"
    )


def test_get_daily_bars_duration():
    """get_daily_bars respects the duration parameter — longer duration = more bars."""
    with Session() as session:
        df_1m = session.market_data.get_daily_bars(PRIMARY_SYMBOL, duration="1 M")
        df_3m = session.market_data.get_daily_bars(PRIMARY_SYMBOL, duration="3 M")

    assert len(df_3m) > len(df_1m), (
        f"3 month fetch ({len(df_3m)} bars) should have more bars than "
        f"1 month fetch ({len(df_1m)} bars)"
    )


def test_get_intraday_bars():
    """get_intraday_bars returns valid intraday data with a timezone-aware index."""
    with Session() as session:
        df = session.market_data.get_intraday_bars(PRIMARY_SYMBOL, bar_size="5 mins", duration="1 W")

    assert_valid_ohlcv(df, "get_intraday_bars 5min")

    # Intraday index should be timezone-aware
    assert df.index.tzinfo is not None, (
        "Intraday bars should have a timezone-aware DatetimeIndex"
    )

    # 1 week of 5-min bars during RTH (6.5 hours/day, 5 days) ≈ 390 bars
    assert len(df) > 50, f"Expected many intraday bars for 1 week, got {len(df)}"


def test_get_bars_passthrough():
    """get_bars works as a general-purpose method with explicit duration and bar_size."""
    with Session() as session:
        df = session.market_data.get_bars(PRIMARY_SYMBOL, duration="1 M", bar_size="1 day")

    assert_valid_ohlcv(df, "get_bars daily")


def test_get_daily_bars_multi():
    """get_daily_bars_multi returns a dict with an entry for each valid symbol."""
    with Session() as session:
        data = session.market_data.get_daily_bars_multi(MULTI_SYMBOLS, duration="1 M")

    assert isinstance(data, dict), f"Expected dict, got {type(data)}"
    assert set(data.keys()) == set(MULTI_SYMBOLS), (
        f"Expected keys {MULTI_SYMBOLS}, got {list(data.keys())}"
    )
    for symbol, df in data.items():
        assert_valid_ohlcv(df, f"get_daily_bars_multi[{symbol}]")


def test_get_close_prices():
    """get_close_prices returns a single aligned DataFrame with one column per symbol."""
    with Session() as session:
        closes = session.market_data.get_close_prices(MULTI_SYMBOLS, duration="1 M")

    assert isinstance(closes, pd.DataFrame), f"Expected DataFrame, got {type(closes)}"
    assert set(closes.columns) == set(MULTI_SYMBOLS), (
        f"Expected columns {MULTI_SYMBOLS}, got {list(closes.columns)}"
    )
    assert not closes.empty, "get_close_prices returned empty DataFrame"
    assert closes.notna().all().all(), "get_close_prices result contains NaN (alignment issue)"


def test_bad_symbol_does_not_crash_multi():
    """A bad symbol in get_daily_bars_multi is skipped — valid symbols still return."""
    symbols = [PRIMARY_SYMBOL, BAD_SYMBOL]

    with Session() as session:
        data = session.market_data.get_daily_bars_multi(symbols, duration="1 M")

    assert PRIMARY_SYMBOL in data, f"{PRIMARY_SYMBOL} should still be in results"
    assert BAD_SYMBOL not in data, f"{BAD_SYMBOL} should have been skipped"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    ("Session connects and disconnects",            test_session_connects),
    ("Session context manager",                     test_session_context_manager),
    ("get_daily_bars — default duration",           test_get_daily_bars_default),
    ("get_daily_bars — duration parameter",         test_get_daily_bars_duration),
    ("get_intraday_bars — 5 min bars",              test_get_intraday_bars),
    ("get_bars — general purpose",                  test_get_bars_passthrough),
    ("get_daily_bars_multi — multiple symbols",     test_get_daily_bars_multi),
    ("get_close_prices — aligned closes",           test_get_close_prices),
    ("bad symbol skipped in multi fetch",           test_bad_symbol_does_not_crash_multi),
]


def main():
    print("\n=== Market Data Integration Tests ===\n")

    passed = 0
    failed = 0

    for name, fn in TESTS:
        result = run_test(name, fn)
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 38}")
    print(f"  {passed} passed  |  {failed} failed  |  {len(TESTS)} total")
    print(f"{'=' * 38}\n")


if __name__ == "__main__":
    main()
    