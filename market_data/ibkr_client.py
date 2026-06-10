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

import threading

import pandas as pd

from contracts.contract_handler import ContractHandler
from database import market_data as _mdb
from market_data.base import MarketDataProvider
from utils.connection_constants import HISTORICAL_DATA_REQUEST_ID
from utils.log_config import setup_logger

logger = setup_logger(__name__)

# Daily bar sizes — datetime column is "YYYYMMDD", no time component
_DAILY_BAR_SIZES = {"1 day", "1 week", "1 month"}

# Intraday reqHistoricalData(formatDate=1) returns timestamps in TWS's configured
# display timezone. This API version emits no timezone label (older versions
# appended a name like "America/Chicago"), so we localize naive timestamps to
# this zone. Change it to match your TWS Time Zone setting
# (Global Configuration > API > Settings). Central is the default here because
# that is what this TWS is configured to (e.g. SPY's 9:30 ET open arrives as 8:30).
DEFAULT_INTRADAY_TZ = "America/Chicago"


class IBKRMarketDataClient(MarketDataProvider):

    def __init__(self, ib_app):
        self.ib = ib_app
        # Serializes concurrent callers: IBApp holds one shared Event + buffer,
        # so overlapping requests would mix their data. Callers that need
        # parallelism must open separate IBApp connections.
        self._request_lock = threading.Lock()

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

        with self._request_lock:
            return self._fetch(symbol, duration, bar_size)

    def _fetch(self, symbol: str, duration: str, bar_size: str) -> pd.DataFrame:
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

        try:
            _mdb.upsert_bars(
                symbol=symbol,
                bars=self.ib.historical_data,
                sec_type=contract.secType,
                bar_size=bar_size,
            )
        except Exception as e:
            logger.warning(f"DB upsert_bars failed for {symbol}: {e}")

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
            # Intraday arrives as "YYYYMMDD HH:MM:SS", optionally followed by a
            # timezone name. The date/time separator may be one or two spaces, so
            # split on whitespace generically rather than a fixed count.
            #   2 tokens -> "YYYYMMDD", "HH:MM:SS"        (no tz label; localize)
            #   3 tokens -> ..., plus a timezone name      (use it directly)
            def _parse_intraday(s: str) -> pd.Timestamp:
                parts = s.split()
                dt = pd.to_datetime(f"{parts[0]} {parts[1]}", format="%Y%m%d %H:%M:%S")
                tz = parts[2] if len(parts) >= 3 else DEFAULT_INTRADAY_TZ
                return dt.tz_localize(tz)

            df["datetime"] = df["datetime"].apply(_parse_intraday)

        df = df.set_index("datetime").sort_index()
        return df
