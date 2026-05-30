import threading
import time

from ibapi.execution import ExecutionFilter

from contracts.contract_handler import ContractHandler
from database import trading as _tdb
from ib_app import IBApp
from orders import order_types
from utils.connection_constants import *
from utils.log_config import setup_logger

logger = setup_logger(__name__)


def connect_orders_handler():
    logger.info("Starting order handler connection...")
    app = IBApp()
    app.connect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, ORDERS_CLIENT_ID)

    thread = threading.Thread(target=app.run, daemon=True)
    thread.start()

    logger.info("Order handler connected. Entering event loop...")

    start = time.time()
    while (time.time() - start) < 5:
        if app.nextOrderId is not None:
            logger.info("Order handler connection established!")
            return app
        time.sleep(0.1)

    raise RuntimeError(
        "Order handler timed out waiting for TWS connection. "
        "Check that no other process is using client ID 0 — see TWS "
        "Edit → Global Configuration → API → Active API Clients."
    )


def request_next_valid_id(app):
    """
    Call this function to request from TWS the next valid ID that
    can be used when placing an order.  After calling this function, the
    nextValidId() event will be triggered, and the id returned is that next
    valid ID. That ID will reflect any autobinding that has occurred (which
    generates new IDs and increments the next valid ID therein).
    """
    app.reqIds(-1)


def request_executions(app):
    """
    When this function is called, the execution reports that meet the
    filter criteria are downloaded to the client via the execDetails()
    function.
    """
    app.reqExecutions(EXECUTIONS_REQUEST_ID, ExecutionFilter())


def request_open_orders(app):
    """
    Call this function to request the open orders that were
    placed from this client. Each open order will be fed back through the
    openOrder() and orderStatus() functions on the EWrapper.
    """
    app.reqOpenOrders()


def request_completed_orders(app):
    """
    Call this function to request the completed orders. If apiOnly parameter
    is true, then only completed orders placed from API are requested.
    Each completed order will be fed back through the
    completedOrder() function on the EWrapper.
    """
    app.reqCompletedOrders(True)


def wait_for_next_id(app, timeout=10):
    """
    Since nextValidId arrives asynchronously, our thread must wait for it.
    Checks nextOrderId directly to avoid consuming an ID during polling.
    """
    start = time.time()
    while True:
        if app.nextOrderId is not None:
            return app.nextOrderId
        if time.time() - start > timeout:
            logger.error("Timed out waiting for nextValidId")
            raise TimeoutError("Timed out waiting for nextValidId")
        time.sleep(0.05)


_UNSET = 1.7976931348623157e+308

def _price(v):
    """Return None if v is the IB unset sentinel or zero (not a meaningful price)."""
    return None if (v is None or v == 0.0 or v >= _UNSET) else v


def place_order(app, contract, order, strategy_name: str = None) -> int:
    """
    Place an order and save it to the database.

    Returns the local database id for the order row so callers can link
    signals or other records to it.
    """
    order_id = app.get_next_order_id()

    is_trail = order.orderType in ("TRAIL", "TRAIL LIMIT")
    is_stop  = order.orderType in ("STP", "STP LMT")

    try:
        db_id = _tdb.save_order(
            symbol=contract.symbol,
            action=order.action,
            order_type=order.orderType,
            quantity=float(order.totalQuantity),
            sec_type=contract.secType,
            tif=order.tif or "DAY",
            limit_price=_price(order.lmtPrice),
            stop_price=_price(order.auxPrice) if is_stop else _price(getattr(order, "trailStopPrice", 0)),
            trail_percent=_price(getattr(order, "trailingPercent", 0)),
            trail_amount=_price(order.auxPrice) if is_trail else None,
            outside_rth=bool(getattr(order, "outsideRth", False)),
            ib_order_id=order_id,
            strategy_name=strategy_name,
        )
    except Exception as e:
        logger.error(f"DB error saving order for {contract.symbol}: {e}")
        db_id = 0

    app.placeOrder(order_id, contract, order)
    return db_id


if __name__ == "__main__":
    app = connect_orders_handler()
    contract = ContractHandler.get_contract("SPY")
    market_order = order_types.market_order("BUY", 2)
    trailing_stop_limit_order = order_types.trailing_stop_limit_order("SELL", 1, 650, 0.50, 10)

    place_order(app, contract, market_order)
    place_order(app, contract, trailing_stop_limit_order)
