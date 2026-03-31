"""
session.py

Provides a single, reusable broker session for research, backtesting, and live trading.

Problem solved
--------------
Every entry point in the codebase (run_backtest.py, run_live.py, run_ibkr_data.py)
duplicates the same connect / thread / wait pattern. In a research context this is
especially painful: you don't want to reconnect to TWS on every script run or notebook
cell execution.

Session encapsulates the entire connection lifecycle once and exposes clean access
to market data and account state. All underlying infrastructure (IBApp, MarketDataService,
connection constants) is reused as-is — Session is purely a coordination layer.

Usage
-----
Basic (data only):

    from research.session import Session

    session = Session()
    df = session.market_data.get_daily_bars("SPY")
    session.disconnect()

With account updates (positions, cash, PnL):

    session = Session(account="U1234567")
    df = session.market_data.get_daily_bars("AAPL")
    position = session.get_position("AAPL")
    cash = session.get_cash_balance()
    session.disconnect()

As a context manager (auto-disconnects):

    with Session(account="U1234567") as session:
        df = session.market_data.get_daily_bars("QQQ")

Notes
-----
- Session uses RESEARCH_CLIENT_ID from connection_constants to avoid colliding
  with live trading (LIVE_ENGINE_CLIENT_ID) or order connections (ORDERS_CLIENT_ID)
- account is optional; if omitted, position and account value methods return None
- Only one account can be subscribed to updates at a time (IB API limitation)
- Session is not thread-safe for concurrent use across multiple threads
"""

import threading
import time

import ib_app as ib_app_module
from market_data.market_data_service import MarketDataService
from positions.position_handler import request_account_updates
from utils.connection_constants import (
    BROKER_CONNECTION_IP,
    BROKER_CONNECTION_PORT,
    RESEARCH_CLIENT_ID,
)
from utils.log_config import setup_logger

logger = setup_logger(__name__)


class Session:
    """
    A managed broker session providing market data and account state.

    Wraps IBApp connection lifecycle so callers never deal with threading,
    event loops, or connection timing directly.

    Attributes
    ----------
    market_data : MarketDataService
        Provides access to historical bar data via get_daily_bars(symbol).

    Parameters
    ----------
    account : str, optional
        IBKR account number (e.g. "U1234567"). When provided, subscribes to
        account updates so position and cash balance methods return live data.
        When omitted, those methods return None.

    timeout : int, optional
        Seconds to wait for TWS to confirm the connection via nextValidId.
        Default: 10.
    """

    def __init__(self, account: str = None, timeout: int = 10):
        self._account = account
        self._timeout = timeout
        self._app = None
        self._thread = None
        self.market_data: MarketDataService = None

        self._connect()

    def _connect(self):
        """
        Establish connection to TWS, start the event loop thread, and wait
        for confirmation before returning. Raises RuntimeError on timeout.
        """
        logger.info("Session connecting to TWS...")

        self._app = ib_app_module.IBApp()
        self._app.connect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, clientId=RESEARCH_CLIENT_ID)

        self._thread = threading.Thread(target=self._app.run, daemon=True)
        self._thread.start()

        self._wait_for_connection()

        self.market_data = MarketDataService(self._app)

        if self._account:
            logger.info(f"Subscribing to account updates for {self._account}")
            request_account_updates(self._app, self._account)

        logger.info("Session ready.")

    def _wait_for_connection(self):
        """
        Block until nextValidId is received, confirming TWS accepted the connection.
        """
        start = time.time()
        while self._app.nextOrderId is None:
            if time.time() - start > self._timeout:
                raise RuntimeError(
                    "Timed out waiting for TWS connection. "
                    "Ensure 'Enable ActiveX and Socket Clients' is checked in "
                    "TWS under Edit -> Global Configuration -> API -> Settings "
                    f"and the socket port matches {BROKER_CONNECTION_PORT}."
                )
            time.sleep(0.1)
        logger.info(f"TWS connection confirmed (nextOrderId={self._app.nextOrderId})")

    # ------------------------------------------------------------------
    # Position access
    # ------------------------------------------------------------------

    def get_position(self, symbol: str) -> float | None:
        """
        Return the current net position size for the given symbol.

        Requires account to have been provided at construction time.
        Data is sourced from updatePortfolio callbacks — reflects the last
        update received from TWS, not a live request.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. "SPY").

        Returns
        -------
        float or None
            Net shares held. 0.0 if no position. None if no account subscribed.
        """
        if not self._account:
            logger.warning("get_position() called but no account was provided to Session")
            return None
        return self._app.get_position(symbol)

    def get_all_positions(self) -> dict | None:
        """
        Return all currently held positions.

        Returns
        -------
        dict or None
            Copy of the positions dict keyed by symbol, or None if no account subscribed.
            Each value contains: position, market_price, market_value, average_cost,
            unrealized_pnl, realized_pnl.
        """
        if not self._account:
            logger.warning("get_all_positions() called but no account was provided to Session")
            return None
        with self._app._account_lock:
            return dict(self._app.positions)

    # ------------------------------------------------------------------
    # Account state access
    # ------------------------------------------------------------------

    def get_cash_balance(self) -> float | None:
        """
        Return current USD cash balance.
        Requires account to have been provided at construction.
        """
        if not self._account:
            return None
        return self._app.get_current_cash_balance()

    def get_unrealized_pnl(self) -> float | None:
        """
        Return current unrealized PnL across all positions.
        Requires account to have been provided at construction.
        """
        if not self._account:
            return None
        return self._app.get_unrealized_pnl()

    def get_realized_pnl(self) -> float | None:
        """
        Return current realized PnL.
        Requires account to have been provided at construction.
        """
        if not self._account:
            return None
        return self._app.get_realized_pnl()

    def get_maintenance_margin(self) -> float | None:
        """
        Return current maintenance margin requirement.
        Requires account to have been provided at construction.
        """
        if not self._account:
            return None
        return self._app.get_current_maintenance_margin()

    # ------------------------------------------------------------------
    # Connection state
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """Return True if the underlying IBApp connection is active."""
        return self._app is not None and self._app.isConnected()

    def disconnect(self):
        """
        Cleanly disconnect from TWS and stop the event loop thread.
        Safe to call multiple times.
        """
        if self._app and self._app.isConnected():
            logger.info("Session disconnecting from TWS...")
            self._app.disconnect()
        self._app = None
        self.market_data = None
        logger.info("Session disconnected.")

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False  # do not suppress exceptions
