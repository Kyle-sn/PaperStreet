import time

from ibapi.execution import ExecutionFilter

from v2.ib_app import IBApp
from v2.utils.connection_constants import *
from v2.utils.log_config import setup_logger

logger = setup_logger(__name__)


def connect_position_handler():
    logger.info("Starting IB connection...")
    app = IBApp()
    # make sure clientId is 0. This is the Master ClientId, which shows all client info
    app.connect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, TRADES_CLIENT_ID)
    logger.info("Connected. Entering event loop...")

    start = time.time()
    while (time.time() - start) < 1:  # wait up to 1 second
        if app.nextOrderId is not None:
            logger.info("IBKR connection established!")
            break
        time.sleep(0.1)
    else:
        logger.error("ERROR: Connection timed out. nextValidId not received.")
    return app


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
    Since nextValidId arrives asynchronously, our thread must wait for it
    """
    start = time.time()
    while True:
        next_id = app.get_next_order_id()
        if next_id is not None:
            return next_id
        if time.time() - start > timeout:
            raise logger.error(TimeoutError("Timed out waiting for nextValidId"))
        time.sleep(0.05)


def place_order(app, contract, order):
    """
    Call this function to place an order. The order status will be returned by the
    orderStatus event.
    """
    order_id = app.get_next_order_id()

    app.placeOrder(order_id, contract, order)

