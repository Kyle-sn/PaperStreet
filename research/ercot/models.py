"""
Data models for the settlement calculator.

SettlementInterval — a single confirmed SPP15 15-minute interval.
RollingEstimate     — a point-in-time rolling settlement estimate snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SettlementInterval:
    """A single confirmed SPP15 15-minute interval."""
    interval_num: int       # 1–4 → :15, :30, :45, :00
    spp15: float
    confirmed_at: datetime

    def to_dict(self) -> dict:
        return {
            "interval_num": self.interval_num,
            "spp15": self.spp15,
            "confirmed_at": self.confirmed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SettlementInterval":
        return cls(
            interval_num=d["interval_num"],
            spp15=d["spp15"],
            confirmed_at=datetime.fromisoformat(d["confirmed_at"]),
        )


@dataclass
class RollingEstimate:
    """A single rolling settlement estimate snapshot."""
    timestamp: datetime
    implied_settlement: float
    bounded_settlement: float
    intervals_realized: int
    intervals_remaining: int
    realized_spp15s: list[float]
    rt_lmp: Optional[float]
    projection_source: str      # "spp15_complete" | "rt_lmp_projection"
    is_final: bool

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "implied_settlement": self.implied_settlement,
            "bounded_settlement": self.bounded_settlement,
            "intervals_realized": self.intervals_realized,
            "intervals_remaining": self.intervals_remaining,
            "realized_spp15s": self.realized_spp15s,
            "rt_lmp": self.rt_lmp,
            "projection_source": self.projection_source,
            "is_final": self.is_final,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RollingEstimate":
        return cls(
            timestamp=datetime.fromisoformat(d["timestamp"]),
            implied_settlement=d["implied_settlement"],
            bounded_settlement=d["bounded_settlement"],
            intervals_realized=d["intervals_realized"],
            intervals_remaining=d["intervals_remaining"],
            realized_spp15s=d["realized_spp15s"],
            rt_lmp=d["rt_lmp"],
            projection_source=d["projection_source"],
            is_final=d["is_final"],
        )
