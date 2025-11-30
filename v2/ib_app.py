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
from v2.utils.log_config import setup_logger

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

    def nextValidId(self, order_id: int):
        """"
        The nextValidId event provides the next valid identifier needed to place an order. It is necessary to use an
        order ID with new orders which is greater than all previous order IDs used to place an order.
        """
        self.nextOrderId = order_id
        logger.info(f"nextOrderId={order_id}")

    def error(self, req_id, error_code, error_string, *args):
        logger.error(f"req_id={req_id}|error_code={error_code}|error_string={error_string}")
        if args:
            logger.error(f"Additional error args: {args}")

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

    def updatePortfolio(self, contract: Contract, position: Decimal, market_price: float, market_value: float,
                        average_cost: float, unrealized_pnl: float, realized_pnl: float, account_name: str):
        """
        Receives the subscribed account’s portfolio. This function will receive only the portfolio
        of the subscribed account. After the initial callback to updatePortfolio, callbacks only
        occur for positions which have changed.
        """
        logger.info(f"symbol={contract.symbol}|sec_type={contract.secType}|exchange=" +
                    f"{contract.exchange}|position={decimalMaxString(position)}|market_price=" +
                    f"{floatMaxString(market_price)}|market_value={floatMaxString(market_value)}|average_cost=" +
                    f"{floatMaxString(average_cost)}|unrealized_PNL={floatMaxString(unrealized_pnl)}" +
                    f"|realized_pnl={floatMaxString(realized_pnl)}|account_name={account_name}")

    def updateAccountTime(self, time_stamp: str):
        """
        Receives the last time on which the account was updated.
        """
        logger.info(f"time_stamp={time_stamp}")

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
        logger.info("Position_End")

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
                    f"mkt_cap_price={mkt_cap_price}")
