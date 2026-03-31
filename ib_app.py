import threading
from decimal import Decimal

from ibapi.client import EClient
from ibapi.commission_and_fees_report import CommissionAndFeesReport
from ibapi.common import OrderId
from ibapi.contract import Contract
from ibapi.execution import Execution
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.utils import decimalMaxString, floatMaxString
from ibapi.wrapper import EWrapper

from utils.log_config import setup_logger

logger = setup_logger(__name__)

"""
The provided TWS API package use two distinct classes to accommodate the request / response 
functionality of the socket protocol, EClient and EWrapper respectively.

The EWrapper class is used to receive all messages from the host and distribute them amongst 
the affiliated response functions. The EReader class will retrieve the messages from the socket 
connection and decode them for distribution by the EWrapper class.
"""


class IBApp(EWrapper, EClient):
    """
    This implements EWrapper callbacks (things IB calls into this app).
    This inherits EClient methods (things this app uses to call IB).

    EWrapper defines all possible callbacks from IBKR:
    - nextValidId (connection/order IDs)
    - tickPrice / tickSize (market data)
    - orderStatus / openOrder (order events)
    - error (any errors)
    - …and many more.

    The base EWrapper class does nothing by default; it’s essentially a template.
    """

    def __init__(self):
        EClient.__init__(self, self)
        self.nextOrderId = None
        self._account_lock = threading.Lock()
        self._id_lock = threading.Lock()
        self.account = {
            "cash_balance": None,
            "maintenance_margin": None,
            "initial_margin": None,
            "realized_pnl": None,
            "unrealized_pnl": None,
        }
        # Keyed by symbol (str). Each value is a dict:
        # {
        #   "position": float,       — net shares held (negative = short)
        #   "market_price": float,
        #   "market_value": float,
        #   "average_cost": float,
        #   "unrealized_pnl": float,
        #   "realized_pnl": float,
        # }
        # Updated by updatePortfolio callbacks (fires on every position change).
        # Positions that are closed (size == 0) are removed from the dict.
        self.positions: dict[str, dict] = {}
        self.historical_data = []
        self._historical_data_event = threading.Event()

    def nextValidId(self, order_id: int):
        """"
        The nextValidId event provides the next valid identifier needed to place an order. It is necessary to use an
        order ID with new orders which is greater than all previous order IDs used to place an order.
        """
        self.nextOrderId = order_id
        logger.info(f"nextOrderId={order_id}")

    def get_next_order_id(self):
        with self._id_lock:
            oid = self.nextOrderId
            self.nextOrderId += 1
            return oid

    def error(self, req_id, error_code, error_string, *args):
        IBKR_INFO_CODES = {
            2104: "Market data farm connection is OK",
            2106: "HMDS data farm connection is OK",
            2158: "Sec-def data farm connection is OK",
        }

        try:
            code_int = int(error_string)
        except ValueError:
            code_int = None

        # If this is an informational message
        if code_int in IBKR_INFO_CODES:
            farm_name = None
            if args and args[0]:
                # args[0] is like "Market data farm connection is OK:cashfarm"
                # Split on ":" to get just the farm
                parts = args[0].split(":")
                if len(parts) > 1:
                    farm_name = parts[1]

            if farm_name:
                logger.info(f"{IBKR_INFO_CODES[code_int]} ({farm_name})")
            else:
                logger.info(f"{IBKR_INFO_CODES[code_int]}")
        else:
            logger.error(f"req_id={req_id}|error_code={error_code}|error_string={error_string}|args={args}")

    def accountSummary(self, req_id: int, account: str, tag: str, value: str, currency: str):
        """
        Receives the account information. This method will receive the account information just as it
        appears in the TWS’ Account Summary Window.
        """
        logger.info(f"req_id={req_id}|account={account}|tag={tag}|value={value}|currency={currency}")

    def accountSummaryEnd(self, req_id: int):
        """
        Notifies when all the accounts’ information has been received. Requires TWS 967+ to receive
        accountSummaryEnd in linked account structures.
        """
        logger.info(f"req_id={req_id}")

    def updateAccountValue(self, key: str, val: str, currency: str, account_name: str):
        """
        Receives the subscribed account’s information. Only one account can be subscribed at a time.
        After the initial callback to updateAccountValue, callbacks only occur for values which have
        changed. This occurs at the time of a position change, or every 3 minutes at most. This
        frequency cannot be adjusted.
        """
        logger.info(f"key={key}|value={val}|currency={currency}|account_name={account_name}")

        if key == "TotalCashBalance" and currency == "USD":
            self.account["cash_balance"] = float(val)
        elif key == "MaintMarginReq":
            self.account["maintenance_margin"] = float(val)
        elif key == "InitMarginReq":
            self.account["initial_margin"] = float(val)
        elif key == "RealizedPnL":
            self.account["realized_pnl"] = float(val)
        elif key == "UnrealizedPNL":
            self.account["unrealized_pnl"] = float(val)

    def get_current_cash_balance(self) -> float | None:
        with self._account_lock:
            return self.account["cash_balance"]

    def get_current_maintenance_margin(self) -> float | None:
        with self._account_lock:
            return self.account["maintenance_margin"]

    def get_current_initial_margin(self) -> float | None:
        with self._account_lock:
            return self.account["initial_margin"]

    def get_realized_pnl(self) -> float | None:
        with self._account_lock:
            return self.account["realized_pnl"]

    def get_unrealized_pnl(self) -> float | None:
        with self._account_lock:
            return self.account["unrealized_pnl"]

    def updatePortfolio(self, contract: Contract, position: Decimal, market_price: float, market_value: float,
                        average_cost: float, unrealized_pnl: float, realized_pnl: float, account_name: str):
        """
        Receives the subscribed account's portfolio. This function will receive only the portfolio
        of the subscribed account. After the initial callback to updatePortfolio, callbacks only
        occur for positions which have changed.

        Position state is stored in self.positions keyed by symbol. Closed positions
        (size == 0) are removed so the dict only contains active holdings.
        """
        logger.info(f"symbol={contract.symbol}|sec_type={contract.secType}|exchange=" +
                    f"{contract.exchange}|position={decimalMaxString(position)}|market_price=" +
                    f"{floatMaxString(market_price)}|market_value={floatMaxString(market_value)}|average_cost=" +
                    f"{floatMaxString(average_cost)}|unrealized_PNL={floatMaxString(unrealized_pnl)}" +
                    f"|realized_pnl={floatMaxString(realized_pnl)}|account_name={account_name}")

        symbol = contract.symbol
        pos_float = float(position)

        with self._account_lock:
            if pos_float == 0:
                # Position closed — remove from tracking dict
                self.positions.pop(symbol, None)
            else:
                self.positions[symbol] = {
                    "position": pos_float,
                    "market_price": market_price,
                    "market_value": market_value,
                    "average_cost": average_cost,
                    "unrealized_pnl": unrealized_pnl,
                    "realized_pnl": realized_pnl,
                }

    def get_position(self, symbol: str) -> float:
        """
        Return the current net position size for the given symbol.

        Returns 0.0 if no position is held (or if updatePortfolio has not yet
        fired for this symbol). Callers should treat this as the broker-confirmed
        position, not an estimate.
        """
        with self._account_lock:
            entry = self.positions.get(symbol)
            return entry["position"] if entry else 0.0

    # def updateAccountTime(self, time_stamp: str):
    #     """
    #     Receives the last time on which the account was updated.
    #     """
    #     logger.info(f"time_stamp={time_stamp}")

    def accountDownloadEnd(self, account_name: str):
        """
        Notifies when all the account’s information has finished.
        """
        logger.info("accountDownloadEnd")

    def position(self, account: str, contract: Contract, position: Decimal, avg_cost: float):
        """
        Provides the portfolio’s open positions. After the initial callback (only) of all positions,
        the IBApi.EWrapper.positionEnd function will be triggered.

        For futures, the exchange field will not be populated in the position callback as some
        futures trade on multiple exchanges
        """
        logger.info(f"account={account}|contract={contract}|position={position}|avg_cost={avg_cost}")

    def positionEnd(self):
        """
        Indicates all the positions have been transmitted. Only returned after the initial callback
        of EWrapper.position.
        """
        logger.info("PositionEnd")

    def commissionAndFeesReport(self, commission_and_fees_report: CommissionAndFeesReport):
        """
        When an order is filled either fully or partially, the IBApi.EWrapper.execDetails and
        IBApi.EWrapper.commissionReport events will deliver IBApi.Execution and
        IBApi.CommissionAndFeesReport objects. This allows to obtain the full picture of the
        order’s execution and the resulting commissions.
        """
        logger.info(commission_and_fees_report)

    def execDetails(self, req_id: int, contract: Contract, execution: Execution):
        """
        Provides the executions which happened in the last 24 hours.
        """
        logger.info(f"req_id={req_id}|symbol={contract.symbol}|sec_type: {contract.secType}" +
                    f"|currency={contract.currency}|execution={execution}")

    def execDetailsEnd(self, req_id: int):
        """
        Indicates the end of the Execution reception.
        """
        logger.info(f"req_id={req_id}")

    def openOrder(self, order_id: OrderId, contract: Contract, order: Order, order_state: OrderState):
        """
        Feeds in currently open orders.
        """
        logger.info(f"order_id={order_id}|contract={contract}|order={order}|order_state={order_state}")

    def openOrderEnd(self):
        """
        Notifies the end of the open orders’ reception.
        """
        logger.info("OpenOrderEnd")

    def orderStatus(self, order_id: OrderId, status: str, filled: Decimal, remaining: Decimal,
                    avg_fill_price: float, perm_id: int, parent_id: int, last_fill_price: float,
                    client_id: int, why_held: str, mkt_cap_price: float):
        """
        This event is called whenever the status of an order
        changes. It is also fired after reconnecting to TWS if the client has any open orders.
        """
        logger.info(f"order_id={order_id}|status={status}|filled={filled}|remaining={remaining}" +
                    f"|avg_fill_price={avg_fill_price}|perm_id={perm_id}|parent_id={parent_id}" +
                    f"|last_fill_price={last_fill_price}|client_id={client_id}|why_held{why_held}" +
                    f"|mkt_cap_price={mkt_cap_price}")

    def completedOrder(self, contract: Contract, order: Order,
                       order_state: OrderState):
        """
        This function is called to feed in completed orders.
        """
        logger.info(f"contract={contract}|order={order}|order_state={order_state}")

    def historicalData(self, reqId, bar):
        self.historical_data.append({
            "datetime": bar.date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
        })

    def historicalDataEnd(self, reqId, start, end):
        logger.info(f"Historical data received: {start} → {end}")
        self._historical_data_event.set()
