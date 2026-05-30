import pandas as pd
from typing import Optional
from .db import get_connection


def upsert_bars(
    symbol: str,
    bars: list[dict],
    sec_type: str = "STK",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
) -> int:
    """Insert bars, skipping any that already exist. Returns number of new rows inserted."""
    sql = """
        INSERT OR IGNORE INTO market_data_bars
            (symbol, sec_type, bar_size, bar_datetime, open, high, low, close, volume, wap, bar_count, what_to_show)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    rows = [
        (
            symbol, sec_type, bar_size, str(b["datetime"]),
            b["open"], b["high"], b["low"], b["close"],
            b.get("volume"), b.get("wap"), b.get("bar_count"),
            what_to_show,
        )
        for b in bars
    ]
    with get_connection() as conn:
        conn.executemany(sql, rows)
        return conn.total_changes


def get_bars(
    symbol: str,
    sec_type: str = "STK",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
) -> Optional[pd.DataFrame]:
    """Return all cached bars for a symbol as a DataFrame (DatetimeIndex), or None if empty."""
    sql = """
        SELECT bar_datetime, open, high, low, close, volume
        FROM market_data_bars
        WHERE symbol = ? AND sec_type = ? AND bar_size = ? AND what_to_show = ?
        ORDER BY bar_datetime ASC
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (symbol, sec_type, bar_size, what_to_show)).fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)
    return df


def get_latest_bar_date(
    symbol: str,
    sec_type: str = "STK",
    bar_size: str = "1 day",
) -> Optional[str]:
    """Return ISO8601 string of the most recent stored bar, or None."""
    sql = """
        SELECT MAX(bar_datetime)
        FROM market_data_bars
        WHERE symbol = ? AND sec_type = ? AND bar_size = ?
    """
    with get_connection() as conn:
        row = conn.execute(sql, (symbol, sec_type, bar_size)).fetchone()
    return row[0] if row else None
