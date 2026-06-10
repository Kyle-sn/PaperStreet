"""
mean_reversion_strategy.py

Implements a spread-based mean reversion strategy with broker-sourced inventory awareness.

Background
----------
Market making profits from the assumption that short-term price deviations from a "fair
value" are temporary and will revert. This strategy approximates that behavior using daily
bar data:

    - Estimate fair value as a rolling SMA of closing prices
    - Compute a dynamic spread threshold based on recent price volatility
    - BUY when price falls sufficiently below fair value (undervalued)
    - SELL when price rises sufficiently above fair value (overvalued)
    - Gate signals against the current position from the broker

Position Sourcing
-----------------
This strategy does NOT track its own position internally. Position is injected at call
time via the `position` parameter of `on_bar`. In live trading, the caller is responsible
for passing the authoritative broker position via IBApp.get_position(symbol), which is
populated by the `updatePortfolio` EWrapper callback.

This eliminates the drift risk that arises from self-tracking (where the strategy's
internal count diverges from reality if the portfolio layer rejects a signal).

For backtesting, position is passed in from Portfolio.position by the engine layer.

Parameters
----------
window : int
    Lookback period for computing the SMA (fair value) and volatility.
    Default: 20

spread_multiplier : float
    Controls how far price must deviate from fair value (as a multiple of volatility)
    before a signal is generated.
    Higher values = fewer, higher-conviction trades.
    Lower values = more frequent trades, noisier signals.
    Default: 1.0

max_position : int
    Hard cap on the number of shares held at any time. Prevents runaway inventory
    accumulation during a trending move.
    Default: 50

order_size : int
    Number of shares per trade.
    Default: 10
"""

from strategy.base_strategy import BaseStrategy
from strategy.indicators import RollingWindow
from strategy.registry import register_strategy
from strategy.signal import OrderRequest
from utils.log_config import setup_logger

logger = setup_logger(__name__)


@register_strategy("mean_reversion")
class MeanReversionStrategy(BaseStrategy):
    """
    Spread-based mean reversion strategy driven by broker-confirmed position data.

    Fair Value
    ----------
    Computed as the simple moving average (SMA) of the most recent `window` closes.

    Spread Threshold
    ----------------
    The entry threshold scales with recent volatility (standard deviation of closing
    prices over `window` bars). This makes the strategy adaptive: it widens the required
    deviation in volatile markets and tightens it in quiet ones.

        threshold = spread_multiplier * std_dev(close prices)

    Signal Logic
    ------------
    Each bar:
        deviation = close - fair_value

        if deviation < -threshold and position < max_position:
            → BUY (price is cheap relative to fair value)

        if deviation > +threshold and position > 0:
            → SELL (price is expensive relative to fair value)

    Inventory Management
    --------------------
    The strategy receives current position as a parameter rather than maintaining its
    own counter. In live trading this comes from IBApp.get_position(), which is updated
    by the updatePortfolio EWrapper callback on every position change. This means the
    strategy's view of inventory is always grounded in broker-confirmed state.

    Attributes
    ----------
    window : int
        Lookback period for SMA and volatility calculation.

    spread_multiplier : float
        Volatility multiplier for the entry threshold.

    max_position : int
        Maximum number of shares the strategy will hold at once.

    order_size : int
        Shares per order.

    prices : RollingWindow
        Bounded rolling history of closing prices (internal indicator state only).
    """

    name = "mean_reversion"

    def __init__(
        self,
        window: int = 20,
        spread_multiplier: float = 1.0,
        max_position: int = 50,
        order_size: int = 10,
    ):
        """
        Initialize the strategy.

        Parameters
        ----------
        window : int
            Number of bars for SMA and volatility calculation. Default: 20.

        spread_multiplier : float
            Multiplier applied to volatility to set the entry threshold. Default: 1.0.

        max_position : int
            Maximum shares the strategy will hold simultaneously. Default: 50.

        order_size : int
            Shares submitted per signal. Default: 10.
        """
        self.window = window
        self.spread_multiplier = spread_multiplier
        self.max_position = max_position
        self.order_size = order_size

        self.prices = RollingWindow(window)

    def on_bar(self, bar: dict, position: float = 0.0) -> OrderRequest | None:
        """
        Process a new bar and generate a trading signal if conditions are met.

        Parameters
        ----------
        bar : dict
            Market data for the current time step.
            Required keys: "datetime", "open", "high", "low", "close", "volume"

        position : float, optional
            Current net position in shares for the instrument being traded.

            In live trading: pass IBApp.get_position(symbol), which reflects
            the last updatePortfolio callback from TWS.

            In backtesting: pass Portfolio.position, which is updated after
            each processed signal.

            Defaults to 0.0 so the signature remains backward-compatible with
            callers that do not supply position.

        Returns
        -------
        OrderRequest or None
            An order to submit, or None if no signal is generated.

        Decision Logic
        --------------
        1. Append close price to internal price history
        2. Return None until the rolling window is full (warm-up)
        3. Compute fair value (SMA) and volatility (std dev)
        4. Compute threshold = spread_multiplier * volatility
        5. Compute deviation = close - fair_value
        6. BUY  if deviation < -threshold and position < max_position
        7. SELL if deviation > +threshold and position > 0
        """
        close_price = bar["close"]
        self.prices.append(close_price)

        # Warm-up: no signal until the window is full
        if not self.prices.ready:
            return None

        fair_value = self.prices.mean()
        volatility = self.prices.std()
        threshold = self.spread_multiplier * volatility
        deviation = close_price - fair_value

        logger.info(
            f"date={bar['datetime']}|close={close_price:.4f}|"
            f"fair_value={fair_value:.4f}|volatility={volatility:.4f}|"
            f"threshold={threshold:.4f}|deviation={deviation:.4f}|"
            f"position={position}"
        )

        # BUY: price is sufficiently below fair value and inventory is not at cap
        if deviation < -threshold and position < self.max_position:
            logger.info(
                f"BUY signal|deviation={deviation:.4f} below -threshold={-threshold:.4f}|"
                f"current position={position}"
            )
            return self.buy(self.order_size)

        # SELL: price is sufficiently above fair value and we hold inventory to sell
        if deviation > threshold and position > 0:
            sell_quantity = min(self.order_size, int(position))
            logger.info(
                f"SELL signal|deviation={deviation:.4f} above threshold={threshold:.4f}|"
                f"current position={position}"
            )
            return self.sell(sell_quantity)

        return None
