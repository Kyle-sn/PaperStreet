"""
moving_average.py

Simple moving-average baseline strategy.

Strategy Logic
--------------
- Maintain a rolling window of recent closing prices
- Compute the simple moving average (SMA) over that window
- BUY  when price > SMA
- SELL when price < SMA

This is a baseline used to validate the backtesting pipeline and demonstrate the
strategy contract. It does not gate on position, so it can repeat the same-side
signal on consecutive bars — the execution layer is responsible for not
over-trading on that.
"""

from strategy.base_strategy import BaseStrategy
from strategy.indicators import RollingWindow
from strategy.registry import register_strategy
from strategy.signal import OrderRequest
from utils.log_config import setup_logger

logger = setup_logger(__name__)


@register_strategy("moving_average")
class MovingAverageStrategy(BaseStrategy):
    """
    SMA crossover-style baseline strategy.

    Parameters
    ----------
    window : int
        Number of bars in the moving average. Default: 5.
    order_size : int
        Shares per signal. Default: 10.
    """

    name = "moving_average"

    def __init__(self, window: int = 5, order_size: int = 10):
        self.window = window
        self.order_size = order_size
        self.prices = RollingWindow(window)

    def on_bar(self, bar: dict, position: float = 0.0) -> OrderRequest | None:
        close_price = bar["close"]
        self.prices.append(close_price)

        # Warm-up: no signal until the window is full
        if not self.prices.ready:
            return None

        moving_average = self.prices.mean()
        logger.info(f"close={close_price}|sma={moving_average}|position={position}")

        if close_price > moving_average:
            return self.buy(self.order_size)
        if close_price < moving_average:
            return self.sell(self.order_size)

        return None
