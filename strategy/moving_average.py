"""
moving_average.py

Implements a simple moving average crossover-style strategy.

Strategy Logic
--------------
- Maintain a rolling window of recent closing prices
- Compute the simple moving average (SMA) over that window
- Generate signals based on price relative to the SMA:

    BUY  -> when price > moving average
    SELL -> when price < moving average

This is a basic example strategy used for:
- validating the backtesting pipeline
- demonstrating how strategies maintain internal state
- providing a simple baseline for further development

TODO: add position awareness
"""

from strategy.base_strategy import BaseStrategy
from utils.log_config import setup_logger

logger = setup_logger(__name__)


class MovingAverageStrategy(BaseStrategy):
    """
    A simple moving average-based trading strategy.

    Attributes
    ----------
    window : int
        Number of periods used to calculate the moving average.

    prices : list[float]
        Stores historical closing prices used for computing the moving average.

    Behavior
    --------
    - Accumulates closing prices as new bars arrive
    - Once enough data is collected (>= window), computes SMA
    - Generates BUY/SELL signals based on price vs SMA
    """

    def __init__(self, window: int = 5):
        """
        Initialize the strategy.

        Parameters
        ----------
        window : int, optional
            Number of bars to include in the moving average calculation.
            Default is 5.
        """
        self.window = window
        self.prices = []

    def on_bar(self, bar: dict) -> dict | None:
        """
        Process a new bar of market data and generate a trading signal.

        Parameters
        ----------
        bar : dict
            A dictionary containing market data for a single time step.
            Expected keys:
            - "datetime"
            - "open"
            - "high"
            - "low"
            - "close"
            - "volume"

        Returns
        -------
        dict or None
            A signal dictionary if a condition is met, otherwise None.

            Example:
            {
                "action": "BUY",
                "quantity": 10
            }

        Strategy Steps
        --------------
        1. Append the latest closing price to internal state
        2. Check if enough data exists to compute moving average
        3. Compute simple moving average (SMA)
        4. Compare current price to SMA:
            - price > SMA → BUY signal
            - price < SMA → SELL signal

        Notes
        -----
        - No signal is generated until enough data is collected
        - This implementation does NOT prevent repeated signals
          (e.g., multiple BUY signals in a row)
        - Position management is handled by the portfolio layer
        """
        close_price = bar["close"]
        self.prices.append(close_price)

        # Not enough data to compute moving average yet
        if len(self.prices) < self.window:
            return None

        # Compute simple moving average (SMA)
        window_prices = self.prices[-self.window:]
        moving_average = sum(window_prices) / self.window
        logger.info(f"Close price: {close_price} | Window prices: {window_prices} | Moving average {moving_average}")

        # Generate trading signal
        if close_price > moving_average:
            return {"action": "BUY", "quantity": 10}

        elif close_price < moving_average:
            return {"action": "SELL", "quantity": 10}

        return None
