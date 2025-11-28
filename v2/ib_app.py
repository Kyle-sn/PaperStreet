from decimal import Decimal

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.utils import decimalMaxString, floatMaxString
from ibapi.wrapper import EWrapper

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

    def nextValidId(self, orderId: int):
        self.nextOrderId = orderId
        print(f"Connected. Next Order ID: {orderId}")

    # Accepts extra arguments to avoid TypeError
    def error(self, reqId, errorCode, errorString, *args):
        print(f"IB Error. ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}")
        if args:
            print("Additional error args:", args)

    def tickPrice(self, reqId, tickType, price, attrib):
        print(f"Tick Price. Ticker Id: {reqId}, Type: {tickType}, Price: {price}")

    def tickSize(self, reqId, tickType, size):
        print(f"Tick Size. Ticker Id: {reqId}, Type: {tickType}, Size: {size}")

    def orderStatus(
            self,
            orderId,
            status,
            filled,
            remaining,
            avgFillPrice,
            permId,
            parentId,
            lastFillPrice,
            clientId,
            whyHeld,
            mktCapPrice,
    ):
        print(f"OrderStatus. ID: {orderId}, Status: {status}, Filled: {filled}")

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        print("AccountSummary. ReqId:", reqId, "Account:", account, "Tag: ", tag, "Value:", value, "Currency:",
              currency)

    def accountSummaryEnd(self, reqId: int):
        print("AccountSummaryEnd. ReqId:", reqId)

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        print("UpdateAccountValue. Key:", key, "Value:", val, "Currency:", currency, "AccountName:", accountName)

    def updatePortfolio(self, contract: Contract, position: Decimal, marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
        print("UpdatePortfolio.", "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:",
              contract.exchange, "Position:", decimalMaxString(position), "MarketPrice:", floatMaxString(marketPrice),
              "MarketValue:", floatMaxString(marketValue), "AverageCost:", floatMaxString(averageCost),
              "UnrealizedPNL:", floatMaxString(unrealizedPNL), "RealizedPNL:", floatMaxString(realizedPNL),
              "AccountName:", accountName)

    def updateAccountTime(self, timeStamp: str):
        print("UpdateAccountTime. Time:", timeStamp)

    def accountDownloadEnd(self, accountName: str):
        print("AccountDownloadEnd. Account:", accountName)

    def position(self, account: str, contract: Contract, position: Decimal, avgCost: float):
        print("Position.", "Account:", account, "Contract:", contract, "Position:", position, "Avg cost:", avgCost)

    def positionEnd(self):
        print("PositionEnd")
