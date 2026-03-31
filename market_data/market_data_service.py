"""
market_data_service.py

Service layer for fetching market data.

Provides convenience methods for common request patterns on top of the
underlying MarketDataProvider. All IBKR-specific details stay in
IBKRMarketDataClient — this layer is about usability.

Multi-symbol fetches are sequential to respect IBKR pacing limits
(60 historical data requests per 10 minutes). Do not parallelize.
"""

import time

import pandas as pd

from market_data.ibkr_client import IBKRMarketDataClient
from utils.log_config import setup_logger

logger = setup_logger(__name__)

# Minimum seconds between requests in a multi-symbol fetch.
# Keeps well within IBKR's 60 requests / 10 min pacing limit.
_MULTI_SYMBOL_DELAY = 0.5


class MarketDataService:

    def __init__(self, ib_app):
        self.provider = IBKRMarketDataClient(ib_app)

    # ------------------------------------------------------------------
    # Single-symbol methods
    # ------------------------------------------------------------------

    def get_daily_bars(self, symbol: str, duration: str = "1 M") -> pd.DataFrame:
        """
        Fetch daily OHLCV bars for a single symbol.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. "SPY").

        duration : str, optional
            Lookback period. Default "1 M".
            Examples: "1 W", "1 M", "3 M", "6 M", "1 Y", "2 Y", "5 Y"

        Returns
        -------
        pd.DataFrame
            Daily OHLCV bars with a DatetimeIndex, sorted oldest-first.
        """
        return self.provider.get_historical_data(symbol, duration=duration, bar_size="1 day")

    def get_intraday_bars(self, symbol: str, bar_size: str = "5 mins", duration: str = "1 W") -> pd.DataFrame:
        """
        Fetch intraday OHLCV bars for a single symbol.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. "SPY").

        bar_size : str, optional
            Bar size. Default "5 mins".
            Options: "1 min", "5 mins", "15 mins", "30 mins", "1 hour"

        duration : str, optional
            Lookback period. Default "1 W".
            Max duration varies by bar size — see base.py for limits.

        Returns
        -------
        pd.DataFrame
            Intraday OHLCV bars with a timezone-aware DatetimeIndex,
            sorted oldest-first.
        """
        return self.provider.get_historical_data(symbol, duration=duration, bar_size=bar_size)

    def get_bars(self, symbol: str, duration: str, bar_size: str) -> pd.DataFrame:
        """
        General-purpose bar fetch. Use when get_daily_bars or get_intraday_bars
        don't cover your exact needs.

        Parameters
        ----------
        symbol : str
            Ticker symbol.

        duration : str
            Lookback period in IBKR format (e.g. "6 M", "1 Y").

        bar_size : str
            Bar size in IBKR format (e.g. "1 day", "1 hour", "15 mins").

        Returns
        -------
        pd.DataFrame
            OHLCV bars with a DatetimeIndex, sorted oldest-first.
        """
        return self.provider.get_historical_data(symbol, duration=duration, bar_size=bar_size)

    # ------------------------------------------------------------------
    # Multi-symbol methods
    # ------------------------------------------------------------------

    def get_daily_bars_multi(self, symbols: list[str], duration: str = "1 M") -> dict[str, pd.DataFrame]:
        """
        Fetch daily bars for multiple symbols sequentially.

        Requests are serialized with a small delay between each to stay within
        IBKR's pacing limits. Do not call this in a tight loop.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols (e.g. ["SPY", "QQQ", "IWM"]).

        duration : str, optional
            Lookback period applied to all symbols. Default "1 M".

        Returns
        -------
        dict[str, pd.DataFrame]
            Symbol → DataFrame mapping. Symbols that fail are logged and
            excluded from the result rather than raising.

        Example
        -------
            data = session.market_data.get_daily_bars_multi(["SPY", "QQQ"], duration="6 M")
            spy_df = data["SPY"]
            qqq_df = data["QQQ"]
        """
        results = {}

        for i, symbol in enumerate(symbols):
            try:
                df = self.get_daily_bars(symbol, duration=duration)
                results[symbol] = df
                logger.info(f"Fetched {symbol} ({i + 1}/{len(symbols)})")
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")

            # Pace requests — skip delay after the last symbol
            if i < len(symbols) - 1:
                time.sleep(_MULTI_SYMBOL_DELAY)

        return results

    def get_close_prices(self, symbols: list[str], duration: str = "1 M") -> pd.DataFrame:
        """
        Fetch closing prices for multiple symbols and align them into a single
        DataFrame. Useful for correlation analysis and relative performance.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols.

        duration : str, optional
            Lookback period applied to all symbols. Default "1 M".

        Returns
        -------
        pd.DataFrame
            DataFrame where each column is a symbol and each row is a date.
            Dates where any symbol has no data are dropped (inner join).

        Example
        -------
            closes = session.market_data.get_close_prices(["SPY", "QQQ", "IWM"], duration="3 M")
            closes.corr()
        """
        data = self.get_daily_bars_multi(symbols, duration=duration)

        if not data:
            raise ValueError("No data returned for any symbol")

        close_series = {symbol: df["close"] for symbol, df in data.items()}
        combined = pd.DataFrame(close_series).dropna()

        logger.info(f"Aligned close prices: {len(combined)} common dates across {list(data.keys())}")
        return combined
