"""
Multi-hub / multi-hour settlement engine.

SettlementEngine — manages HourlySettlementCalculator instances across
all active hubs and contract hours.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from .hourly_calculator import HourlySettlementCalculator
from .models import RollingEstimate

logger = logging.getLogger(__name__)


class SettlementEngine:
    """
    Manages HourlySettlementCalculator instances across all active hubs
    and contract hours simultaneously.

    A (hub, contract_hour_ending) pair is called a *key* throughout.

    Typical flow
    ------------
        engine = SettlementEngine(hubs=["HB_NORTH", "HB_HOUSTON"])

        # Broadcast an RT LMP update to all active hours for a hub
        engine.broadcast_rt_lmp("HB_NORTH", lmp=47.50)

        # Confirm an SPP15 for a specific hub + hour
        engine.confirm_spp15("HB_NORTH", hour_ending=16, interval_num=1, spp15=44.10)

        # Retrieve the current estimate for any key
        est = engine.latest_estimate("HB_NORTH", hour_ending=16)

        # Serialize entire engine state to JSON
        engine.save("state.json")

        # Restore
        engine2 = SettlementEngine.load("state.json")
    """

    DEFAULT_HUBS = [
        "HB_NORTH",
        "HB_HOUSTON",
        "HB_SOUTH",
        "HB_WEST",
    ]

    def __init__(
        self,
        hubs: Optional[list[str]] = None,
        price_floor: float = -250.0,
        price_cap: float = 5000.0,
    ):
        """
        Parameters
        ----------
        hubs : list of str, optional
            Hubs to track. Defaults to the five standard ERCOT trading hubs.
        price_floor / price_cap : float
            Applied to every calculator created by this engine.
        """
        self.hubs: list[str] = hubs or list(self.DEFAULT_HUBS)
        self.price_floor = price_floor
        self.price_cap = price_cap

        # (hub, hour_ending) → HourlySettlementCalculator
        self._calculators: dict[tuple[str, int], HourlySettlementCalculator] = {}

    # -- calculator lifecycle ------------------------------------------------

    def get_or_create(
        self,
        hub: str,
        hour_ending: int,
    ) -> HourlySettlementCalculator:
        """Return an existing calculator or create a new one for the key."""
        key = (hub, hour_ending)
        if key not in self._calculators:
            if hub not in self.hubs:
                logger.warning(
                    f"Hub {hub} is not in the registered hub list — creating anyway."
                )
            self._calculators[key] = HourlySettlementCalculator(
                hub=hub,
                contract_hour_ending=hour_ending,
                price_floor=self.price_floor,
                price_cap=self.price_cap,
            )
            # logger.info(f"Created calculator: {hub} HE{hour_ending}")
        return self._calculators[key]

    def get(
        self,
        hub: str,
        hour_ending: int,
    ) -> Optional[HourlySettlementCalculator]:
        """Return an existing calculator, or None if it hasn't been created yet."""
        return self._calculators.get((hub, hour_ending))

    def active_keys(self) -> list[tuple[str, int]]:
        """All (hub, hour_ending) pairs currently tracked."""
        return list(self._calculators.keys())

    def drop(self, hub: str, hour_ending: int) -> None:
        """Remove a finalized or stale calculator to free memory."""
        key = (hub, hour_ending)
        if key in self._calculators:
            label = self._calculators[key]._label()
            del self._calculators[key]
            logger.info(f"Dropped calculator: {label}")

    def drop_finalized(self) -> list[tuple[str, int]]:
        """Remove all calculators whose settlement is final. Returns dropped keys."""
        dropped = [k for k, c in self._calculators.items() if c.is_final]
        for k in dropped:
            del self._calculators[k]
        if dropped:
            logger.info(f"Dropped {len(dropped)} finalized calculators.")
        return dropped

    # -- data ingestion ------------------------------------------------------

    def update_rt_lmp(
        self,
        hub: str,
        hour_ending: int,
        lmp: float,
        as_of: Optional[datetime] = None,
    ) -> Optional[RollingEstimate]:
        """
        Feed an RT LMP update to a specific hub + hour.
        Creates the calculator if it doesn't exist yet.
        """
        return self.get_or_create(hub, hour_ending).update_rt_lmp(lmp, as_of)

    def broadcast_rt_lmp(
        self,
        hub: str,
        lmp: float,
        as_of: Optional[datetime] = None,
    ) -> dict[int, Optional[RollingEstimate]]:
        """
        Broadcast one RT LMP to all active hours for a given hub.

        Useful when a feed delivers a single hub price that applies to
        whatever hours are currently open.

        Returns
        -------
        dict mapping hour_ending → RollingEstimate (or None if already final).
        """
        results = {}
        for (h, he), calc in self._calculators.items():
            if h == hub:
                results[he] = calc.update_rt_lmp(lmp, as_of)
        return results

    def broadcast_rt_lmp_all_hubs(
        self,
        lmp_by_hub: dict[str, float],
        hour_ending: int,
        as_of: Optional[datetime] = None,
    ) -> dict[str, Optional[RollingEstimate]]:
        """
        Feed RT LMPs for multiple hubs at once for the same hour.

        Parameters
        ----------
        lmp_by_hub : dict[hub_name → lmp_value]
        hour_ending : int
            The contract hour these prices apply to.

        Returns
        -------
        dict mapping hub → RollingEstimate.
        """
        results = {}
        for hub, lmp in lmp_by_hub.items():
            results[hub] = self.update_rt_lmp(hub, hour_ending, lmp, as_of)
        return results

    def confirm_spp15(
        self,
        hub: str,
        hour_ending: int,
        interval_num: int,
        spp15: float,
        confirmed_at: Optional[datetime] = None,
    ) -> Optional[RollingEstimate]:
        """Confirm a single SPP15 interval for a hub + hour."""
        return self.get_or_create(hub, hour_ending).confirm_spp15(
            interval_num, spp15, confirmed_at
        )

    def broadcast_spp15(
        self,
        interval_num: int,
        spp15_by_hub: dict[str, float],
        hour_ending: int,
        confirmed_at: Optional[datetime] = None,
    ) -> dict[str, RollingEstimate]:
        """
        Confirm the same SPP15 interval across multiple hubs simultaneously.

        Parameters
        ----------
        interval_num : int
            Interval 1–4.
        spp15_by_hub : dict[hub_name → spp15_value]
        hour_ending : int

        Returns
        -------
        dict mapping hub → RollingEstimate.
        """
        results = {}
        for hub, spp15 in spp15_by_hub.items():
            results[hub] = self.confirm_spp15(
                hub, hour_ending, interval_num, spp15, confirmed_at
            )
        return results

    def replace_spp15(
        self,
        hub: str,
        hour_ending: int,
        interval_num: int,
        spp15: float,
        confirmed_at: Optional[datetime] = None,
    ) -> RollingEstimate:
        """Override an already-confirmed SPP15 (e.g. ERCOT resettlement correction)."""
        return self.get_or_create(hub, hour_ending).replace_spp15(
            interval_num, spp15, confirmed_at
        )

    # -- queries -------------------------------------------------------------

    def latest_estimate(
        self,
        hub: str,
        hour_ending: int,
    ) -> Optional[RollingEstimate]:
        """Most recent rolling estimate for a key, or None."""
        calc = self.get(hub, hour_ending)
        return calc.latest_estimate if calc else None

    def all_latest_estimates(self) -> dict[tuple[str, int], Optional[RollingEstimate]]:
        """Latest estimate for every tracked (hub, hour_ending) pair."""
        return {k: c.latest_estimate for k, c in self._calculators.items()}

    def final_settlement(self, hub: str, hour_ending: int) -> float:
        """Return the exact final settlement price. Raises if not yet final."""
        calc = self.get(hub, hour_ending)
        if calc is None:
            raise KeyError(f"No calculator found for {hub} HE{hour_ending}.")
        return calc.final_settlement()

    def finalized_settlements(self) -> dict[tuple[str, int], float]:
        """Return final settlement prices for all completed hours."""
        return {
            k: c.final_settlement()
            for k, c in self._calculators.items()
            if c.is_final
        }

    def pending_keys(self) -> list[tuple[str, int]]:
        """Keys where settlement is not yet final."""
        return [k for k, c in self._calculators.items() if not c.is_final]

    def summary(self) -> list[dict]:
        """Summary snapshot for all tracked calculators, sorted by hub + hour."""
        return [
            c.summary()
            for (hub, he), c in sorted(self._calculators.items())
        ]

    # -- serialization -------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "hubs": self.hubs,
            "price_floor": self.price_floor,
            "price_cap": self.price_cap,
            "calculators": {
                f"{hub}|{he}": calc.to_dict()
                for (hub, he), calc in self._calculators.items()
            },
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SettlementEngine":
        engine = cls(
            hubs=d["hubs"],
            price_floor=d["price_floor"],
            price_cap=d["price_cap"],
        )
        for key_str, calc_dict in d["calculators"].items():
            hub, he_str = key_str.split("|")
            he = int(he_str)
            engine._calculators[(hub, he)] = HourlySettlementCalculator.from_dict(
                calc_dict
            )
        return engine

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "SettlementEngine":
        return cls.from_dict(json.loads(json_str))

    def save(self, path: str) -> None:
        """Persist engine state to a JSON file."""
        with open(path, "w") as f:
            f.write(self.to_json())
        logger.info(f"SettlementEngine state saved to {path}")

    @classmethod
    def load(cls, path: str) -> "SettlementEngine":
        """Restore engine state from a JSON file."""
        with open(path) as f:
            return cls.from_json(f.read())
