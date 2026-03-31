"""
ibkr_client.py

Concrete MarketDataProvider implementation backed by the IBKR TWS API.

Responsibilities
----------------
- Translate MarketDataProvider calls into reqHistoricalData requests
- Wait for the asynchronous IBKR response
- Parse and clean the raw response into a well-formed DataFrame:
    - datetime string → parsed DatetimeIndex
    - daily bars   → date-only index (no time component)
    - intraday bars → timezone-aware DatetimeIndex
- Raise clearly on timeout or empty response

Notes
-----
- Requests are synchronous from the caller's perspective (blocks until data arrives)
- The shared _historical_data_event / historical_data state on IBApp means
  concurrent requests on the same connection are not safe — callers must
  serialize requests (MarketDataService handles this for multi-symbol fetches)
- IBKR pacing limit: 60 historical data requests per 10 minutes
"""

import pandas as pd

from contracts.contract_handler import ContractHandler
from market_data.base import MarketDataProvider
from utils.connection_constants import HISTORICAL_DATA_REQUEST_ID
from utils.log_config import setup_logger

logger = setup_logger(__name__)

# Daily bar sizes — datetime column is "YYYYMMDD", no time component
_DAILY_BAR_SIZES = {"1 day", "1 week", "1 month"}


class IBKRMarketDataClient(MarketDataProvider):

    def __init__(self, ib_app):
        self.ib = ib_app

    def get_historical_data(self, symbol: str, duration: str, bar_size: str) -> pd.DataFrame:
        """
        Fetch historical bar data from IBKR for a single symbol.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. "SPY").

        duration : str
            Lookback period in IBKR format (e.g. "1 M", "1 Y", "6 M").

        bar_size : str
            Bar size in IBKR format (e.g. "1 day", "5 mins", "1 hour").

        Returns
        -------
        pd.DataFrame
            OHLCV DataFrame with a DatetimeIndex, sorted oldest-first.

        Raises
        ------
        ValueError
            If no data is returned within the timeout window.
        """
        logger.info(f"Requesting historical data: symbol={symbol} duration={duration} bar_size={bar_size}")

        contract = ContractHandler.get_contract(symbol)

        # Reset shared state before each request
        self.ib.historical_data = []
        self.ib._historical_data_event.clear()

        self.ib.reqHistoricalData(
            reqId=HISTORICAL_DATA_REQUEST_ID,
            contract=contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=1,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )

        self.ib._historical_data_event.wait(timeout=10)

        if not self.ib.historical_data:
            raise ValueError(
                f"No data returned for {symbol} "
                f"(duration={duration}, bar_size={bar_size}). "
                "Check that the symbol is valid and the duration/bar_size "
                "combination is supported by IBKR."
            )

        df = pd.DataFrame(self.ib.historical_data)
        df = self._parse_datetime_index(df, bar_size)

        logger.info(f"Received {len(df)} bars for {symbol}")
        return df

    def _parse_datetime_index(self, df: pd.DataFrame, bar_size: str) -> pd.DataFrame:
        """
        Parse the raw datetime string from IBKR into a proper DatetimeIndex.

        Daily bars arrive as "YYYYMMDD" — converted to date-only index.
        Intraday bars arrive as "YYYYMMDD HH:MM:SS America/Chicago" (or similar
        timezone) — converted to a timezone-aware DatetimeIndex.

        Parameters
        ----------
        df : pd.DataFrame
            Raw DataFrame with a string "datetime" column.

        bar_size : str
            Used to determine whether this is a daily or intraday request.

        Returns
        -------
        pd.DataFrame
            Same data with "datetime" parsed and set as the index,
            sorted chronologically.
        """
        if bar_size in _DAILY_BAR_SIZES:
            df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d")
        else:
            # Intraday: "20260330 09:30:00 America/Chicago"
            # Split off the timezone name, parse the datetime, then localize
            def _parse_intraday(s: str) -> pd.Timestamp:
                parts = s.rsplit(" ", 1)
                dt = pd.to_datetime(parts[0], format="%Y%m%d %H:%M:%S")
                if len(parts) == 2:
                    dt = dt.tz_localize(parts[1])
                return dt

            df["datetime"] = df["datetime"].apply(_parse_intraday)

        df = df.set_index("datetime").sort_index()
        return df
