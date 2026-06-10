"""
indicators.py

Shared, bounded rolling-window state for strategies.

Every bar strategy needs the same thing: keep the last N closes and compute
simple statistics off them. Doing this with a plain list (as the early
strategies did) leaks memory in a long-running live loop because the list grows
without bound. `RollingWindow` is backed by a `collections.deque` with a fixed
`maxlen`, so memory is constant regardless of how long the strategy runs.
"""

from __future__ import annotations

from collections import deque


class RollingWindow:
    """
    Fixed-size rolling window of float values with O(1) append.

    Once `size` values have been seen the oldest is evicted on each append, so
    the window always holds at most `size` values. `ready` is True once it is
    full — strategies should suppress signals until then (warm-up).

    Parameters
    ----------
    size : int
        Number of most-recent values to retain.
    """

    def __init__(self, size: int):
        if size <= 0:
            raise ValueError(f"size must be positive, got {size}")
        self.size = size
        self._values: deque[float] = deque(maxlen=size)

    def append(self, value: float) -> None:
        self._values.append(value)

    @property
    def ready(self) -> bool:
        """True once the window holds a full `size` values."""
        return len(self._values) == self.size

    @property
    def last(self) -> float:
        return self._values[-1]

    def mean(self) -> float:
        return sum(self._values) / len(self._values)

    def std(self) -> float:
        """
        Population standard deviation of the current window.

        Population (divide by N) rather than sample (N-1) matches the original
        MeanReversionStrategy behavior. Returns 0.0 when all values are equal.
        """
        n = len(self._values)
        mean = sum(self._values) / n
        variance = sum((v - mean) ** 2 for v in self._values) / n
        return variance ** 0.5

    def __len__(self) -> int:
        return len(self._values)
