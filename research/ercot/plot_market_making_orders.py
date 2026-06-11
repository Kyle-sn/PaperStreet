#!/usr/bin/env python3
"""Plot ERCOT market making output and implied settlement.

Usage:
    python plot_market_making_orders.py [input_csv] [--output plot.png] [--last-hours H]

Columns in input expected:
- timestamp_utc, hub, settlement_date, hour_ending, implied_settlement, bid, offer
"""

from __future__ import annotations

import argparse
import csv
import datetime
import sys
from pathlib import Path
from typing import Optional


def _load_data(path: Path):
    try:
        import pandas as pd

        df = pd.read_csv(path, parse_dates=["timestamp_utc"] )
        if "timestamp_utc" not in df.columns:
            raise ValueError("timestamp_utc required")
        df = df.sort_values("timestamp_utc")
        return df
    except ImportError:
        # fallback to csv module
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                if not row.get("timestamp_utc"):
                    continue
                rows.append({
                    "timestamp_utc": datetime.datetime.fromisoformat(row["timestamp_utc"]),
                    "hub": row.get("hub", ""),
                    "settlement_date": row.get("settlement_date", ""),
                    "hour_ending": int(row.get("hour_ending", 0)),
                    "implied_settlement": float(row.get("implied_settlement", "nan")),
                    "bid": float(row.get("bid", "nan")),
                    "offer": float(row.get("offer", "nan")),
                })
        # minimal lightweight frame-like
        return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot market making orders CSV")
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Input CSV file path (default: Downloads/market_making_orders.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="market_making_orders.png",
        help="Output plot image path",
    )
    parser.add_argument(
        "--last-hours",
        type=float,
        default=None,
        help="Only plot the last H hours of data",
    )
    parser.add_argument(
        "--hub",
        default=None,
        help="Filter by hub (default: all hubs)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    input_path = (
        Path(args.input)
        if args.input is not None
        else Path.home() / "Downloads" / "market_making_orders.csv"
    )
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError as exc:
        raise RuntimeError(
            "This script requires pandas and matplotlib. Install via: pip install pandas matplotlib"
        ) from exc

    df = pd.read_csv(input_path, parse_dates=["timestamp_utc"])

    if args.hub is not None:
        df = df[df["hub"] == args.hub]

    df = df.sort_values("timestamp_utc")

    if args.last_hours is not None and args.last_hours > 0:
        now = df["timestamp_utc"].max()
        cutoff = now - pd.Timedelta(hours=args.last_hours)
        df = df[df["timestamp_utc"] >= cutoff]

    if df.empty:
        raise RuntimeError("No data to plot after applying filters")

    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(df["timestamp_utc"], df["implied_settlement"], label="Implied", color="black", linewidth=1.5)
    ax.plot(df["timestamp_utc"], df["bid"], label="Bid", color="tab:green", alpha=0.7)
    ax.plot(df["timestamp_utc"], df["offer"], label="Offer", color="tab:red", alpha=0.7)

    ax.fill_between(df["timestamp_utc"], df["bid"], df["offer"], color="tab:gray", alpha=0.10)

    ax.set_title(
        f"Market Making Orders {'('+args.hub+')' if args.hub else ''} - {input_path.name}",
        fontsize=14,
    )
    ax.set_ylabel("Price")
    ax.set_xlabel("UTC Timestamp")
    ax.grid(True, alpha=0.35)

    ax.legend(loc="upper left")

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    fig.autofmt_xdate(rotation=30)

    if args.verbose:
        print(f"Input rows: {len(df)}")
        print(f"Output path: {args.output}")
    plt.tight_layout()
    fig.savefig(args.output, dpi=150)

    print(f"Plot saved to: {args.output}")


if __name__ == "__main__":
    main()
