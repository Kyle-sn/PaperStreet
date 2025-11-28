from decimal import Decimal

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.utils import decimalMaxString, floatMaxString
from ibapi.wrapper import EWrapper
from v2.log_config import setup_logger

logger = setup_logger(__name__)

"""
The provided TWS API package use two distinct classes to accommodate the request / response functionality of the 
socket protocol, EClient and EWrapper respectively.

The EWrapper class is used to receive all messages from the host and distribute them amongst the affiliated response 
functions. The EReader class will retrieve the messages from the socket connection and decode them for distribution 
by the EWrapper class.
"""


class IBApp(EWrapper, EClient):
    """
    EWrapper is the IBKR callback interface.

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
        self.nextOrderId = order_id
        logger.info(f"Connected. Next Order ID: {order_id}")

    # Accepts extra arguments to avoid TypeError
    def error(self, req_id, error_code, error_string, *args):
        logger.error(f"IB Error. ReqId: {req_id}, Code: {error_code}, Msg: {error_string}")
        if args:
            logger.error(f"Additional error args: {args}")

    def accountSummary(self, req_id: int, account: str, tag: str, value: str, currency: str):
        """
        Receives the account information. This method will receive the account information just as it
        appears in the TWS’ Account Summary Window.
        """
        logger.info(f"ReqId: {req_id}, Account: {account}, Tag: {tag}, Value: {value}, Currency: {currency}")

    def accountSummaryEnd(self, req_id: int):
        """
        Notifies when all the accounts’ information has ben received. Requires TWS 967+ to receive
        accountSummaryEnd in linked account structures.
        """
        logger.info(f"ReqId: {req_id}")

    def updateAccountValue(self, key: str, val: str, currency: str, account_name: str):
        """
        Receives the subscribed account’s information. Only one account can be subscribed at a time.
        After the initial callback to updateAccountValue, callbacks only occur for values which have
        changed. This occurs at the time of a position change, or every 3 minutes at most. This
        frequency cannot be adjusted.
        """
        logger.info(f"Key: {key}, Value: {val}, Currency: {currency}, Account_Name: {account_name}")

    def updatePortfolio(self, contract: Contract, position: Decimal, market_price: float, market_value: float,
                        average_cost: float, unrealized_pnl: float, realized_pnl: float, account_name: str):
        """
        Receives the subscribed account’s portfolio. This function will receive only the portfolio
        of the subscribed account. After the initial callback to updatePortfolio, callbacks only
        occur for positions which have changed.
        """
        logger.info(f"Symbol: {contract.symbol}, Sec_Type: {contract.secType}, Exchange: " +
                    f"{contract.exchange}, Position: {decimalMaxString(position)}, Market_Price: " +
                    f"{floatMaxString(market_price)}, Market_Value: {floatMaxString(market_value)}, Average_Cost: " +
                    f"{floatMaxString(average_cost)}, Unrealized_PNL: {floatMaxString(unrealized_pnl)}, " +
                    f"Realized_PNL: {floatMaxString(realized_pnl)}, Account_Name: {account_name}")

    def updateAccountTime(self, time_stamp: str):
        """
        Receives the last time on which the account was updated.
        """
        logger.info(f"Time: {time_stamp}")

    def accountDownloadEnd(self, account_name: str):
        """
        Notifies when all the account’s information has finished.
        """
        logger.info(f"Account: {account_name}")

    def position(self, account: str, contract: Contract, position: Decimal, avg_cost: float):
        """
        Provides the portfolio’s open positions. After the initial callback (only) of all positions,
        the IBApi.EWrapper.positionEnd function will be triggered.

        For futures, the exchange field will not be populated in the position callback as some
        futures trade on multiple exchanges
        """
        logger.info(f"Account: {account}, Contract: {contract}, Position: {position}, Avg cost: {avg_cost}")

    def positionEnd(self):
        """
        Indicates all the positions have been transmitted. Only returned after the initial callback
        of EWrapper.position.
        """
        logger.info("Position_End")
