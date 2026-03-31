"""
base.py

Abstract interface for market data providers.

Any concrete implementation (IBKR, CSV, synthetic) must implement
get_historical_data so it can be used interchangeably by MarketDataService.
"""

from abc import ABC, abstractmethod
import pandas as pd


class MarketDataProvider(ABC):

    @abstractmethod
    def get_historical_data(self, symbol: str, duration: str, bar_size: str) -> pd.DataFrame:
        """
        Fetch historical bar data for a single symbol.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. "SPY").

        duration : str
            How far back to fetch. IBKR format examples:
            "1 D", "1 W", "1 M", "3 M", "6 M", "1 Y", "2 Y", "5 Y"

        bar_size : str
            Size of each bar. IBKR format examples:
            "1 min", "5 mins", "15 mins", "30 mins", "1 hour", "1 day", "1 week"

            Valid duration / bar_size combinations (IBKR enforced):
            +-----------+------------------------------------------------------+
            | Bar size  | Max duration                                         |
            +-----------+------------------------------------------------------+
            | 1 min     | 1 W                                                  |
            | 5 mins    | 1 M                                                  |
            | 15 mins   | 1 M                                                  |
            | 30 mins   | 1 M                                                  |
            | 1 hour    | 1 Y                                                  |
            | 1 day     | 5 Y                                                  |
            | 1 week    | 5 Y                                                  |
            +-----------+------------------------------------------------------+

        Returns
        -------
        pd.DataFrame
            OHLCV data with columns: open, high, low, close, volume.
            Index is a DatetimeIndex (timezone-aware for intraday, date for daily).
            Sorted chronologically (oldest first).
        """
        pass
