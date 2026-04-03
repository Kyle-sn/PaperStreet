#!/usr/bin/env python3
"""Load LMP5/SPP15 test data and merge events for settlement engine replay."""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

ERCOT_TZ = ZoneInfo("America/Chicago")

LMP_TIMESTAMP_KEYS = ["sced_timestamp_utc", "interval_end_utc", "timestamp_utc", "as_of", "time"]
LMP_LMP_KEYS = ["lmp", "rt_lmp", "price", "lmps" "lmp5"]
HUB_KEYS = ["hub", "location", "node", "price_point"]
SPP_TIMESTAMP_KEYS = ["interval_end_utc", "confirmed_at", "timestamp_utc", "time"]
SPP_SPP15_KEYS = ["spp15", "spp", "price"]
SPP_INTERVAL_KEYS = ["interval_num", "interval", "interval_number", "interval_index"]
SPP_HE_KEYS = ["hour_ending", "he", "hour"]
SPP_SETTLEMENT_DATE_KEYS = ["settlement_date", "date"]


def _coalesce(row: Dict[str, str], keys: List[str]) -> Optional[str]:
    for key in keys:
        if key in row and row[key] not in (None, "", "NA", "na"):
            return row[key]
        low = key.lower()
        for k2, v in row.items():
            if k2.lower() == low and v not in (None, "", "NA", "na"):
                return v
    return None


def _parse_datetime(value: str) -> datetime:
    if value is None or str(value).strip() == "":
        raise ValueError("Empty datetime string")
    raw = str(value).strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    raw = raw.replace(" ", "T")
    # Some inputs may use / separators or no time zone.
    if "+0000" in raw and "+00:00" not in raw:
        raw = raw.replace("+0000", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except Exception as exc:
        try:
            dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S")
            dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            raise ValueError(f"Unable to parse datetime: {value!r}") from exc

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _infer_hour_ending_and_settlement_date_from_interval_end(interval_end_utc: datetime) -> Tuple[int, date]:
    ct = interval_end_utc.astimezone(ERCOT_TZ)
    minute = ct.minute

    if minute == 0:
        # 00:00 belongs to HE24 of previous day in ERCOT conventions
        if ct.hour == 0:
            return 24, (ct.date() - timedelta(days=1))
        return ct.hour, ct.date()

    # For all other times, this belongs to the ongoing hour's HE
    he = ct.hour + 1 if ct.hour < 23 else 24
    return he, ct.date()


def _infer_interval_num_from_interval_end(interval_end_utc: datetime) -> int:
    minute = interval_end_utc.astimezone(ERCOT_TZ).minute
    if minute == 15:
        return 1
    if minute == 30:
        return 2
    if minute == 45:
        return 3
    if minute == 0:
        return 4
    raise ValueError(f"Cannot infer SPP15 interval from minute {minute}")


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if any(v is not None and str(v).strip() != "" for v in r.values())]
    return rows


def _read_lmp5_events(lmp5_csv: Path, hub_filter: Optional[str]) -> List[Tuple[datetime, str, Dict[str, Any]]]:
    rows = _read_csv_rows(lmp5_csv)
    events: List[Tuple[datetime, str, Dict[str, Any]]] = []

    for row in rows:
        hub = _coalesce(row, HUB_KEYS) or hub_filter
        if hub_filter and hub and hub.upper() != hub_filter.upper():
            continue
        if hub is None:
            raise ValueError("Unable to determine hub for LMP row; specify hub_filter")

        lmp_str = _coalesce(row, LMP_LMP_KEYS)
        if lmp_str is None:
            raise ValueError("Unable to determine LMP value from row")
        lmp = float(lmp_str)

        ts_str = _coalesce(row, LMP_TIMESTAMP_KEYS)
        if ts_str is None:
            raise ValueError("Unable to determine timestamp for LMP row")
        as_of = _parse_datetime(ts_str)

        hour_ending = None
        settlement_date = None

        he_str = _coalesce(row, SPP_HE_KEYS)
        if he_str is not None:
            hour_ending = int(he_str)

        settlement_date_str = _coalesce(row, SPP_SETTLEMENT_DATE_KEYS)
        if settlement_date_str is not None:
            settlement_date = date.fromisoformat(settlement_date_str)

        if hour_ending is None or settlement_date is None:
            he, sd = _infer_hour_ending_and_settlement_date_from_interval_end(as_of)
            hour_ending = hour_ending or he
            settlement_date = settlement_date or sd

        payload = {
            "hub": hub,
            "hour_ending": int(hour_ending),
            "settlement_date": settlement_date,
            "lmp": float(lmp),
            "as_of": as_of,
        }

        events.append((as_of, "lmp", payload))

    return events


def _read_spp15_events(spp15_csv: Path, hub_filter: Optional[str]) -> List[Tuple[datetime, str, Dict[str, Any]]]:
    rows = _read_csv_rows(spp15_csv)
    events: List[Tuple[datetime, str, Dict[str, Any]]] = []

    for row in rows:
        hub = _coalesce(row, HUB_KEYS) or hub_filter
        if hub_filter and hub and hub.upper() != hub_filter.upper():
            continue
        if hub is None:
            raise ValueError("Unable to determine hub for SPP15 row; specify hub_filter")

        spp15_str = _coalesce(row, SPP_SPP15_KEYS)
        if spp15_str is None:
            raise ValueError("Unable to determine SPP15 value from row")
        spp15 = float(spp15_str)

        ts_str = _coalesce(row, SPP_TIMESTAMP_KEYS)
        if ts_str is None:
            raise ValueError("Unable to determine timestamp for SPP15 row")
        confirmed_at = _parse_datetime(ts_str)

        interval_num = None
        interval_num_str = _coalesce(row, SPP_INTERVAL_KEYS)
        if interval_num_str is not None:
            interval_num = int(interval_num_str)

        hour_ending = None
        he_str = _coalesce(row, SPP_HE_KEYS)
        if he_str is not None:
            hour_ending = int(he_str)

        settlement_date = None
        sd_str = _coalesce(row, SPP_SETTLEMENT_DATE_KEYS)
        if sd_str is not None:
            settlement_date = date.fromisoformat(sd_str)

        interval_end_str = _coalesce(row, ["interval_end_utc", "interval_end", "as_of", "timestamp_utc"])
        if interval_end_str is not None:
            interval_end = _parse_datetime(interval_end_str)
            if interval_num is None:
                try:
                    interval_num = _infer_interval_num_from_interval_end(interval_end)
                except ValueError:
                    pass
            if hour_ending is None or settlement_date is None:
                he, sd = _infer_hour_ending_and_settlement_date_from_interval_end(interval_end)
                hour_ending = hour_ending or he
                settlement_date = settlement_date or sd

        if interval_num is None:
            raise ValueError("Unable to determine SPP15 interval number from row")
        if hour_ending is None or settlement_date is None:
            raise ValueError("Unable to determine hour_ending/settlement_date for SPP15 row")

        payload = {
            "hub": hub,
            "hour_ending": int(hour_ending),
            "settlement_date": settlement_date,
            "interval_num": int(interval_num),
            "spp15": float(spp15),
            "confirmed_at": confirmed_at,
        }

        events.append((confirmed_at, "spp15", payload))

    return events


def load_and_merge_events(
    lmp5_csv: str,
    spp15_csv: str,
    hub_filter: Optional[str] = None,
) -> List[Tuple[datetime, str, Dict[str, Any]]]:
    lmp5_path = Path(lmp5_csv)
    spp15_path = Path(spp15_csv)
    if not lmp5_path.exists():
        raise FileNotFoundError(f"LMP5 CSV not found: {lmp5_path}")
    if not spp15_path.exists():
        raise FileNotFoundError(f"SPP15 CSV not found: {spp15_path}")

    lmp_events = _read_lmp5_events(lmp5_path, hub_filter)
    spp15_events = _read_spp15_events(spp15_path, hub_filter)

    events = sorted(
        [*lmp_events, *spp15_events],
        key=lambda ev: (ev[0], 0 if ev[1] == "lmp" else 1),
    )

    return events


def main() -> None:
    parser = argparse.ArgumentParser(description="Load and check settlement test data event stream")
    parser.add_argument("lmp5_csv", help="LMP5 source CSV")
    parser.add_argument("spp15_csv", help="SPP15 source CSV")
    parser.add_argument("--hub", default="HB_NORTH", help="Hub filter")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logs")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    events = load_and_merge_events(args.lmp5_csv, args.spp15_csv, hub_filter=args.hub)
    logging.info("Loaded %d events", len(events))
    for i, (ts, kind, payload) in enumerate(events[:5], 1):
        logging.info("%03d %s %s %s", i, ts.isoformat(), kind, payload)

    print("Loaded", len(events), "events")


if __name__ == "__main__":
    main()
