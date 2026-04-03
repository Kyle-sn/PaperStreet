"""
ercot_market_making_strategy.py

Market making strategy driven by ERCOT implied settlement prices.

Background
----------
This strategy quotes a two-sided market (bid and offer) around the implied
settlement price produced by the HourlySettlementCalculator / SettlementEngine.
It is designed for use with ERCOT front-hour bounded futures contracts and is
NOT tied to the IBKR infrastructure used by other strategies in this repo.

The implied settlement is computed as:
    - A weighted average of confirmed SPP15 prices (15-min settlement intervals)
    - Remaining intervals projected using the latest 5-min RT LMP

As more SPP15 intervals confirm across the hour, the projection uncertainty
shrinks and the strategy tightens its spread accordingly.

Quote Width
-----------
Spread is driven by two parameters:

    base_spread_pct       — half-spread at full confidence (4/4 SPP15s confirmed)
    spread_multiplier_max — multiplier applied at zero confidence (0/4 confirmed)

The multiplier scales linearly from spread_multiplier_max down to 1.0 as each
SPP15 confirms. A hard cap applies regardless:

    max_total_spread = max(max_spread_pct * mid, max_spread_abs)

If the uncapped spread exceeds this, it is clamped to the cap, centered on mid.

Floor Rule
----------
The product being quoted has a floor of $0. If implied settlement is at or
below zero, bid is forced to $0. The offer continues to be computed normally
above zero.

Data Staleness Guard
--------------------
If no estimate has been received within `stale_threshold_seconds`, the strategy
returns None and stops quoting. This protects against quoting on stale data
when the LMP or SPP15 feed is delayed or interrupted.

Inventory Management
--------------------
Position is injected via `on_estimate` — the strategy does not self-track.

    max_position : int
        Hard cap in MWh. If abs(position) >= max_position, no quote is returned.

    quote_size : int
        Normal quantity quoted on each side (default 10 MWh).

At 50% of max_position in either direction, the quote size on the side that
would increase inventory is reduced by 2 contracts. This begins tightening
inventory accumulation before the hard cap is reached.

    Example (max_position=50, quote_size=10):
        position >= 25  → bid size reduced to 8, offer size stays at 10
        position <= -25 → offer size reduced to 8, bid size stays at 10

Parameters
----------
base_spread_pct : float
    Half-spread percentage at 4/4 SPP15s confirmed. Default: 0.02 (2%).

spread_multiplier_max : float
    Spread multiplier at 0/4 SPP15s confirmed. Default: 7.0.

max_spread_pct : float
    Maximum allowed total spread as a fraction of mid. Default: 0.20 (20%).

max_spread_abs : float
    Minimum floor on the total spread cap in $/MWh. Default: 8.0.

max_position : int
    Hard inventory cap in MWh (absolute value). Default: 50.

quote_size : int
    Normal quote size in MWh per side. Default: 10.

stale_threshold_seconds : int
    Maximum seconds without a new estimate before quoting is suspended.
    Default: 1200 (20 minutes).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from utils.log_config import setup_logger

logger = setup_logger(__name__)

N_INTERVALS = 4


class ERCOTMarketMakingStrategy:
    """
    Two-sided market making strategy driven by ERCOT implied settlement estimates.

    This strategy does not inherit from BaseStrategy — its interface is purpose-built
    for settlement-based quoting rather than OHLCV bar consumption. It is intended
    for use outside the IBKR infrastructure.

    Quote Format
    ------------
    on_estimate() always returns a quote dict (never None under normal conditions):

        {
            "bid":          float,   — bid price
            "offer":        float,   — offer price
            "bid_size":     int,     — quantity to buy (MWh)
            "offer_size":   int,     — quantity to sell (MWh)
            "mid":          float,   — midpoint of bid/offer
            "spread":       float,   — total spread (offer - bid)
            "spread_pct":   float,   — spread as fraction of mid
            "implied":      float,   — implied settlement used
            "intervals":    int,     — SPP15 intervals confirmed at time of quote
            "source":       str,     — projection_source from the estimate
            "timestamp":    datetime — timestamp of the estimate
        }

    Returns None when quoting is suppressed:
        - No estimate received yet
        - Last estimate is stale (> stale_threshold_seconds old)
        - abs(position) >= max_position

    Attributes
    ----------
    base_spread_pct : float
    spread_multiplier_max : float
    max_spread_pct : float
    max_spread_abs : float
    max_position : int
    quote_size : int
    stale_threshold_seconds : int
    """

    def __init__(
        self,
        base_spread_pct: float = 0.02,
        spread_multiplier_max: float = 7.0,
        max_spread_pct: float = 0.20,
        max_spread_abs: float = 8.0,
        max_position: int = 50,
        quote_size: int = 10,
        stale_threshold_seconds: int = 1200,
    ):
        self.base_spread_pct = base_spread_pct
        self.spread_multiplier_max = spread_multiplier_max
        self.max_spread_pct = max_spread_pct
        self.max_spread_abs = max_spread_abs
        self.max_position = max_position
        self.quote_size = quote_size
        self.stale_threshold_seconds = stale_threshold_seconds

        self._last_estimate_time: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def on_estimate(
        self,
        estimate,
        position: float = 0.0,
        as_of: Optional[datetime] = None,
    ) -> Optional[dict]:
        """
        Process a new RollingEstimate and return a two-sided quote.

        Parameters
        ----------
        estimate : RollingEstimate
            The latest rolling settlement estimate from HourlySettlementCalculator
            or SettlementEngine. Must expose:
                - implied_settlement : float
                - intervals_realized : int
                - projection_source  : str
                - timestamp          : datetime

        position : float, optional
            Current net inventory in MWh. Positive = long, negative = short.
            Injected by the caller — this strategy does not self-track position.
            Defaults to 0.0.

        as_of : datetime, optional
            Wall-clock time used to evaluate data staleness. Defaults to UTC now.
            Pass explicitly in backtesting to use event time rather than real time.

        Returns
        -------
        dict or None
            Quote dict if quoting is active, None if suppressed.

        Suppression conditions
        ----------------------
        - No estimate received yet (should not occur if called correctly)
        - Last estimate timestamp is stale (gap > stale_threshold_seconds)
        - abs(position) >= max_position (hard inventory cap breached)
        """
        now = as_of or datetime.now(timezone.utc)
        self._last_estimate_time = estimate.timestamp

        # --- Staleness check ---
        age_seconds = (now - estimate.timestamp).total_seconds()
        if age_seconds > self.stale_threshold_seconds:
            logger.warning(
                f"Estimate is stale ({age_seconds:.0f}s old, threshold={self.stale_threshold_seconds}s) "
                f"— suspending quote."
            )
            return None

        # --- Hard inventory cap ---
        if abs(position) >= self.max_position:
            logger.warning(
                f"Position limit reached (position={position}, max={self.max_position}) "
                f"— suspending quote."
            )
            return None

        implied = estimate.implied_settlement
        intervals = estimate.intervals_realized

        bid, offer = self._compute_bid_offer(implied, intervals)
        bid_size, offer_size = self._compute_quote_sizes(position)

        mid = (bid + offer) / 2
        spread = offer - bid
        spread_pct = round(spread / mid, 6) if mid != 0 else None

        quote = {
            "bid":        bid,
            "offer":      offer,
            "bid_size":   bid_size,
            "offer_size": offer_size,
            "mid":        round(mid, 4),
            "spread":     round(spread, 4),
            "spread_pct": spread_pct,
            "implied":    implied,
            "intervals":  intervals,
            "source":     estimate.projection_source,
            "timestamp":  estimate.timestamp,
        }

        logger.info(
            f"Quote|implied={implied:.4f}|intervals={intervals}/4|"
            f"bid={bid:.4f}|offer={offer:.4f}|"
            f"bid_size={bid_size}|offer_size={offer_size}|"
            f"spread={spread:.4f}|position={position}|"
            f"source={estimate.projection_source}"
        )

        return quote

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_bid_offer(self, implied: float, intervals_realized: int) -> tuple[float, float]:
        """
        Compute bid and offer prices around the implied settlement.

        Steps
        -----
        1. Compute the spread multiplier based on how many SPP15s are confirmed.
           Scales linearly from spread_multiplier_max (0 confirmed) to 1.0 (4 confirmed).
        2. Compute uncapped half-spread: base_spread_pct * multiplier.
        3. Derive uncapped bid/offer and their midpoint.
        4. Apply hard spread cap: max(max_spread_pct * mid, max_spread_abs).
           If uncapped spread exceeds cap, re-center bid/offer around mid at cap width.
        5. Apply floor rule: if implied <= 0, force bid to $0.

        Returns
        -------
        tuple[float, float]
            (bid, offer) rounded to 4 decimal places.
        """
        unfilled = N_INTERVALS - min(max(intervals_realized, 0), N_INTERVALS)
        mult = 1.0 + (self.spread_multiplier_max - 1.0) * (unfilled / N_INTERVALS)
        half_pct = self.base_spread_pct * mult

        bid   = implied * (1 - half_pct)
        offer = implied * (1 + half_pct)
        mid   = (bid + offer) / 2

        # Apply hard spread cap
        max_total_spread = max(self.max_spread_pct * mid, self.max_spread_abs)
        actual_spread    = offer - bid

        if actual_spread > max_total_spread:
            half_dollar = max_total_spread / 2
            bid   = mid - half_dollar
            offer = mid + half_dollar

        # Floor rule: product cannot be quoted below $0
        if implied <= 0:
            bid = 0.0
            logger.info(
                f"Implied settlement at or below zero ({implied:.4f}) — bid floored to $0."
            )

        return round(bid, 4), round(offer, 4)

    def _compute_quote_sizes(self, position: float) -> tuple[int, int]:
        """
        Compute bid and offer quote sizes based on current inventory.

        At or beyond 50% of max_position in either direction, the size on the
        side that would further increase inventory is reduced by 2 contracts.

        Parameters
        ----------
        position : float
            Current net position in MWh.

        Returns
        -------
        tuple[int, int]
            (bid_size, offer_size)
        """
        half_limit = self.max_position * 0.5
        size_reduction = 2

        bid_size   = self.quote_size
        offer_size = self.quote_size

        if position >= half_limit:
            # Long inventory building — reduce bid size to slow accumulation
            bid_size = max(0, self.quote_size - size_reduction)
        elif position <= -half_limit:
            # Short inventory building — reduce offer size to slow accumulation
            offer_size = max(0, self.quote_size - size_reduction)

        return bid_size, offer_size
