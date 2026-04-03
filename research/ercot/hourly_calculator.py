"""
Per-hour settlement calculator.

HourlySettlementCalculator — tracks and computes rolling implied settlement
for a single (hub, contract hour), using confirmed SPP15s and RT LMP projections.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

import logging

from .models import RollingEstimate, SettlementInterval
from ._utils import ERCOT_TZ, format_settlement_label

logger = logging.getLogger(__name__)


class HourlySettlementCalculator:
    """
    Tracks and computes the rolling implied settlement price for a single
    ElectronX bounded futures contract hour at a given ERCOT hub.

    Settlement = arithmetic mean of 4 SPP15 prices for the contract hour.
    While SPP15s are pending, remaining intervals are projected using the
    latest 5-min RT LMP.

    Parameters
    ----------
    hub : str
        ERCOT settlement point hub, e.g. "HB_NORTH", "HB_HOUSTON".
    contract_hour_ending : int
        Hour ending 1–24. HE16 = the hour 15:00–16:00.
    price_floor : float
        Bounded contract floor. Default -250.
    price_cap : float
        Bounded contract cap. Default 5000.
    """

    N_INTERVALS = 4
    INTERVAL_LABELS = {1: ":15", 2: ":30", 3: ":45", 4: ":00"}

    def __init__(
        self,
        hub: str,
        contract_hour_ending: int,
        price_floor: float = -250.0,
        price_cap: float = 5000.0,
    ):
        self.hub = hub
        self.contract_hour_ending = contract_hour_ending
        self.price_floor = price_floor
        self.price_cap = price_cap

        self._rt_lmp: Optional[float] = None
        self._rt_lmp_updated_at: Optional[datetime] = None
        self._confirmed_intervals: dict[int, SettlementInterval] = {}
        self._estimate_history: list[RollingEstimate] = []
        self._settlement_date: Optional[date] = None  # ERCOT Central date, set from first event

    def _label(self) -> str:
        """Log label including hub, settlement date, and HE (e.g. 'HB_NORTH March 10 HE19')."""
        return format_settlement_label(self.hub, self.contract_hour_ending, self._settlement_date)

    def _set_settlement_date(self, dt: datetime) -> None:
        """Set settlement date from event timestamp (ERCOT Central)."""
        if self._settlement_date is None:
            self._settlement_date = dt.astimezone(ERCOT_TZ).date()

    # -- public interface ----------------------------------------------------

    def update_rt_lmp(
        self,
        lmp: float,
        as_of: Optional[datetime] = None,
    ) -> Optional[RollingEstimate]:
        """
        Record a new 5-min RT LMP and recompute the rolling estimate.

        Returns None once settlement is already final (all 4 SPP15s confirmed).
        """
        if self.is_final:
            logger.debug(
                f"{self._label()} already final — ignoring RT LMP update."
            )
            return None

        self._rt_lmp = lmp
        self._rt_lmp_updated_at = as_of or datetime.now(timezone.utc)
        self._set_settlement_date(self._rt_lmp_updated_at)
        return self._compute_and_record(as_of=self._rt_lmp_updated_at)

    def confirm_spp15(
        self,
        interval_num: int,
        spp15: float,
        confirmed_at: Optional[datetime] = None,
    ) -> Optional[RollingEstimate]:
        """
        Record a confirmed SPP15 for one of the four 15-min intervals.

        Parameters
        ----------
        interval_num : int
            1–4, mapping to :15, :30, :45, :00 within the hour.
        spp15 : float
            Confirmed SPP15 price.
        confirmed_at : datetime, optional
            Timestamp of confirmation. Defaults to UTC now.

        Returns
        -------
        RollingEstimate or None
            Rolling estimate after this confirmation, or None if there is no
            RT LMP yet and the final implied settlement cannot be computed.
        """
        if interval_num not in range(1, self.N_INTERVALS + 1):
            raise ValueError(f"interval_num must be 1–4, got {interval_num}.")

        if interval_num in self._confirmed_intervals:
            existing = self._confirmed_intervals[interval_num].spp15
            raise ValueError(
                f"Interval {interval_num} ({self.INTERVAL_LABELS[interval_num]}) "
                f"already confirmed for {self._label()} "
                f"with spp15={existing}. Use replace_spp15() to override."
            )

        ts = confirmed_at or datetime.now(timezone.utc)
        self._set_settlement_date(ts)
        self._confirmed_intervals[interval_num] = SettlementInterval(
            interval_num=interval_num,
            spp15=spp15,
            confirmed_at=ts,
        )

        return self._compute_and_record(as_of=ts)

    def replace_spp15(
        self,
        interval_num: int,
        spp15: float,
        confirmed_at: Optional[datetime] = None,
    ) -> Optional[RollingEstimate]:
        """
        Override an already-confirmed SPP15 (e.g. ERCOT correction/resettlement).
        Logs a warning and recomputes.
        """
        if interval_num in self._confirmed_intervals:
            old = self._confirmed_intervals[interval_num].spp15
            logger.warning(
                f"Replacing SPP15 for {self._label()} interval {interval_num}: {old:.4f} → {spp15:.4f}"
            )
            del self._confirmed_intervals[interval_num]

        return self.confirm_spp15(interval_num, spp15, confirmed_at)

    @property
    def is_final(self) -> bool:
        """True once all 4 SPP15 intervals have been confirmed."""
        return len(self._confirmed_intervals) == self.N_INTERVALS

    def final_settlement(self) -> float:
        """
        Return the exact bounded settlement price.
        Raises RuntimeError if not all 4 intervals are confirmed.
        """
        if not self.is_final:
            n = len(self._confirmed_intervals)
            raise RuntimeError(
                f"Settlement not final — {n}/4 SPP15 intervals confirmed for "
                f"{self.hub} HE{self.contract_hour_ending}."
            )
        return self._estimate_history[-1].bounded_settlement

    @property
    def latest_estimate(self) -> Optional[RollingEstimate]:
        """Most recent rolling estimate, or None if no updates fed yet."""
        return self._estimate_history[-1] if self._estimate_history else None

    @property
    def estimate_history(self) -> list[RollingEstimate]:
        """Full list of rolling estimates, oldest first."""
        return list(self._estimate_history)

    def summary(self) -> dict:
        """Human-readable snapshot of current state."""
        est = self.latest_estimate
        return {
            "hub": self.hub,
            "contract_hour_ending": self.contract_hour_ending,
            "settlement_date": (
                self._settlement_date.isoformat()
                if self._settlement_date else None
            ),
            "label": self._label(),
            "price_bounds": [self.price_floor, self.price_cap],
            "confirmed_intervals": {
                k: {"spp15": v.spp15, "confirmed_at": v.confirmed_at.isoformat()}
                for k, v in sorted(self._confirmed_intervals.items())
            },
            "rt_lmp": self._rt_lmp,
            "rt_lmp_updated_at": (
                self._rt_lmp_updated_at.isoformat()
                if self._rt_lmp_updated_at else None
            ),
            "is_final": self.is_final,
            "latest_implied_settlement": est.implied_settlement if est else None,
            "latest_bounded_settlement": est.bounded_settlement if est else None,
            "n_estimates_recorded": len(self._estimate_history),
        }

    # -- serialization -------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "hub": self.hub,
            "contract_hour_ending": self.contract_hour_ending,
            "price_floor": self.price_floor,
            "price_cap": self.price_cap,
            "rt_lmp": self._rt_lmp,
            "rt_lmp_updated_at": (
                self._rt_lmp_updated_at.isoformat()
                if self._rt_lmp_updated_at else None
            ),
            "settlement_date": (
                self._settlement_date.isoformat()
                if self._settlement_date else None
            ),
            "confirmed_intervals": {
                str(k): v.to_dict()
                for k, v in self._confirmed_intervals.items()
            },
            "estimate_history": [e.to_dict() for e in self._estimate_history],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HourlySettlementCalculator":
        calc = cls(
            hub=d["hub"],
            contract_hour_ending=d["contract_hour_ending"],
            price_floor=d["price_floor"],
            price_cap=d["price_cap"],
        )
        calc._rt_lmp = d["rt_lmp"]
        calc._rt_lmp_updated_at = (
            datetime.fromisoformat(d["rt_lmp_updated_at"])
            if d["rt_lmp_updated_at"] else None
        )
        if d.get("settlement_date"):
            calc._settlement_date = date.fromisoformat(d["settlement_date"])
        calc._confirmed_intervals = {
            int(k): SettlementInterval.from_dict(v)
            for k, v in d["confirmed_intervals"].items()
        }
        calc._estimate_history = [
            RollingEstimate.from_dict(e) for e in d["estimate_history"]
        ]
        return calc

    # -- internal ------------------------------------------------------------

    def _realized_spp15s(self) -> list[float]:
        return [
            self._confirmed_intervals[i].spp15
            for i in sorted(self._confirmed_intervals)
        ]

    def _compute_and_record(self, as_of: datetime) -> RollingEstimate:
        realized = self._realized_spp15s()
        intervals_realized = len(realized)
        intervals_remaining = self.N_INTERVALS - intervals_realized

        if intervals_remaining == 0:
            implied = sum(realized) / self.N_INTERVALS
            projection_source = "spp15_complete"
        else:
            if self._rt_lmp is None:
                # RT LMP not yet available; use latest confirmed SPP15 as proxy.
                # This ensures we can continue generating orders when SPP updates
                # arrive ahead of first RT LMP.
                proxy = realized[-1] if realized else 0.0
                projection_source = "spp15_rtproxy"
            else:
                proxy = self._rt_lmp
                projection_source = "rt_lmp_projection"

            implied = (
                sum(realized) + proxy * intervals_remaining
            ) / self.N_INTERVALS

        bounded = max(self.price_floor, min(self.price_cap, implied))

        estimate = RollingEstimate(
            timestamp=as_of,
            implied_settlement=round(implied, 4),
            bounded_settlement=round(bounded, 4),
            intervals_realized=intervals_realized,
            intervals_remaining=intervals_remaining,
            realized_spp15s=list(realized),
            rt_lmp=self._rt_lmp,
            projection_source=projection_source,
            is_final=(intervals_remaining == 0),
        )
        self._estimate_history.append(estimate)
        # logger.info(
        #     f"Current implied settlement: {self._label()} "
        #     f"implied={estimate.implied_settlement:.4f} bounded={estimate.bounded_settlement:.4f} "
        #     f"({projection_source}, {intervals_realized}/4 intervals, is_final={estimate.is_final})"
        # )
        return estimate
