"""
base_quoting_strategy.py

The contract for two-sided *quoting* strategies — a distinct family from the
bar-driven BaseStrategy. A quoting strategy continuously prices a market (bid
and offer) around some fair value rather than emitting discrete BUY/SELL signals
off OHLCV bars. The ERCOT market maker is the first member.

It is kept separate (rather than forced into on_bar) because the input and the
output differ fundamentally: it consumes settlement *estimates* and returns a
*quote* dict, not OHLCV bars and OrderRequests. Sharing one interface would
contort both.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class BaseQuotingStrategy(ABC):
    """
    Abstract base class for settlement/estimate-driven quoting strategies.

    Attributes
    ----------
    name : str
        Unique identifier, set by @register_quoting_strategy or as a class attr.
    """

    name: str = ""

    @abstractmethod
    def on_estimate(self, estimate, position: float = 0.0,
                    as_of: Optional[datetime] = None) -> Optional[dict]:
        """
        Process a new fair-value estimate and return a two-sided quote.

        Parameters
        ----------
        estimate : object
            Latest estimate (e.g. RollingEstimate). Shape is strategy-specific.
        position : float
            Current net inventory. Injected by the caller; not self-tracked.
        as_of : datetime, optional
            Wall-clock time for staleness checks. Defaults to now; pass event
            time in backtests.

        Returns
        -------
        dict | None
            A quote dict, or None when quoting is suppressed (stale data,
            inventory cap, etc.).
        """
        ...

    # ------------------------------------------------------------------
    # Lifecycle hooks — override as needed; default to no-ops
    # ------------------------------------------------------------------

    def on_start(self) -> None:
        """Called once when the strategy starts."""

    def on_stop(self) -> None:
        """Called once when the strategy stops."""
