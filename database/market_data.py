import sqlite3
import pandas as pd
from typing import Optional
from .db import get_connection

# Bar sizes whose datetime is a calendar date with no intraday time component.
_DAILY_BAR_SIZES = {"1 day", "1 week", "1 month"}


def _normalize_bar_datetime(value, bar_size: str) -> str:
    """Coerce any supported datetime representation into a canonical ISO 8601 string.

    Bars have historically reached the DB in two shapes: raw IBKR strings
    ("20260312" for daily, "20260609  08:30:00" for intraday) from the live fetch
    path, and ISO strings ("2026-03-12") from other callers. Because bar_datetime
    is part of the UNIQUE key, those two shapes produced *duplicate* rows for the
    same bar and broke reads (pandas inferred one format then choked on the other).
    Normalizing here, at the single write boundary, makes storage consistent
    regardless of caller.

    Daily/weekly/monthly bars -> date only ("YYYY-MM-DD").
    Intraday bars -> full ISO timestamp, preserving a timezone offset if present.
    """
    if isinstance(value, str):
        s = value.strip()
        if len(s) == 8 and s.isdigit():
            # Raw IBKR daily: "YYYYMMDD"
            ts = pd.to_datetime(s, format="%Y%m%d")
        elif len(s) >= 8 and s[:8].isdigit() and " " in s:
            # Raw IBKR intraday: "YYYYMMDD HH:MM:SS [TZ]" (one or two spaces).
            parts = s.split()
            ts = pd.to_datetime(f"{parts[0]} {parts[1]}", format="%Y%m%d %H:%M:%S")
            if len(parts) >= 3:
                ts = ts.tz_localize(parts[2])
        else:
            # Already ISO (or otherwise parseable) — let pandas infer.
            ts = pd.to_datetime(s)
    else:
        ts = pd.Timestamp(value)

    if bar_size in _DAILY_BAR_SIZES:
        return ts.date().isoformat()
    return ts.isoformat()


def upsert_bars(
    symbol: str,
    bars: list[dict],
    sec_type: str = "STK",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
) -> int:
    """Insert bars, skipping any that already exist. Returns number of new rows inserted.

    bar_datetime is normalized to a canonical ISO string (see _normalize_bar_datetime)
    so that the UNIQUE key dedups correctly no matter what format the caller supplies.
    """
    sql = """
        INSERT OR IGNORE INTO market_data_bars
            (symbol, sec_type, bar_size, bar_datetime, open, high, low, close, volume, wap, bar_count, what_to_show)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    rows = [
        (
            symbol, sec_type, bar_size, _normalize_bar_datetime(b["datetime"], bar_size),
            b["open"], b["high"], b["low"], b["close"],
            b.get("volume"), b.get("wap"), b.get("bar_count"),
            what_to_show,
        )
        for b in bars
    ]
    with get_connection() as conn:
        conn.executemany(sql, rows)
        return conn.total_changes


def migrate_bar_datetimes() -> int:
    """Rewrite any non-canonical bar_datetime values to canonical ISO, de-duplicating.

    Self-heals databases written before _normalize_bar_datetime existed (which may
    hold the same bar twice under "20260312" and "2026-03-12"). Idempotent: once all
    rows are canonical it makes no changes. Returns the number of rows updated.
    Called from initialize_db so existing databases fix themselves on startup.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, bar_size, bar_datetime FROM market_data_bars"
        ).fetchall()
        updated = 0
        for row in rows:
            canonical = _normalize_bar_datetime(row["bar_datetime"], row["bar_size"])
            if canonical == row["bar_datetime"]:
                continue
            try:
                conn.execute(
                    "UPDATE market_data_bars SET bar_datetime = ? WHERE id = ?",
                    (canonical, row["id"]),
                )
                updated += 1
            except sqlite3.IntegrityError:
                # The canonical form already exists for this bar — drop the duplicate.
                conn.execute("DELETE FROM market_data_bars WHERE id = ?", (row["id"],))
        return updated


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
    # format="mixed" tolerates legacy rows still in raw "YYYYMMDD" form alongside
    # the canonical ISO that upsert_bars now writes. After migrate_bar_datetimes
    # runs, all rows are ISO and this is a single inferred format.
    df["datetime"] = pd.to_datetime(df["datetime"], format="mixed")
    df.set_index("datetime", inplace=True)
    # The SQL ORDER BY sorts bar_datetime as text, which is only chronological for
    # canonical ISO. Sort by the parsed timestamps so order holds even if legacy
    # raw rows are still present (pre-migration).
    df.sort_index(inplace=True)
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
