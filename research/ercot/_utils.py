"""Shared constants and helpers for the settlement calculator."""

from __future__ import annotations

from datetime import date
from typing import Optional
from zoneinfo import ZoneInfo

# ERCOT settlement date is in Central time
ERCOT_TZ = ZoneInfo("America/Chicago")


def format_settlement_label(hub: str, hour_ending: int, settlement_date: Optional[date] = None) -> str:
    """Format hub + date + HE for logging, e.g. 'HB_NORTH March 10 HE19'."""
    if settlement_date is None:
        return f"{hub} HE{hour_ending}"
    month_day = f"{settlement_date.strftime('%B')} {settlement_date.day}"
    return f"{hub} {month_day} HE{hour_ending}"
