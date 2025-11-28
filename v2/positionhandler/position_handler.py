import time

from ibapi.account_summary_tags import AccountSummaryTags

from v2.ib_app import IBApp
from v2.connection_constants import *
from v2.log_config import setup_logger

logger = setup_logger(__name__)


def connect_position_handler():
    logger.info("Starting IB connection...")
    app = IBApp()
    app.connect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, clientId=0)
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


def request_account_summary(app):
    """
    Requests a specific account’s summary.

    The initial invocation of reqAccountSummary will result in a list of all requested values being
    returned, and then every three minutes those values which have changed will be returned. The
    update frequency of 3 minutes is the same as the TWS Account Window and cannot be changed.
    """
    logger.info("Requesting account summary")
    app.reqAccountSummary(1, "All", AccountSummaryTags.AllTags)


def request_account_updates(app, account):
    """
    Subscribes to a specific account’s information and portfolio. Through this method, a single
    account’s subscription can be started/stopped. As a result from the subscription, the account’s
    information, portfolio and last update time will be received at EWrapper.updateAccountValue,
    EWrapper.updatePortfolio, EWrapper.updateAccountTime respectively. All account values and
    positions will be returned initially, and then there will only be updates when there is a
    change in a position, or to an account value every 3 minutes if it has changed. Only one account
    can be subscribed at a time.
    """
    logger.info("Requesting account updates")
    app.reqAccountUpdates(True, account)


def request_positions(app):
    """
    Subscribes to position updates for all accessible accounts. All positions sent initially, and
    then only updates as positions change.
    """
    logger.info("Requesting positions")
    app.reqPositions()


if __name__ == "__main__":
    app = connect_position_handler()
    request_account_summary(app)
    request_account_updates(app, "ADD_ACCOUNT_NUMBER_HERE")
    request_positions(app)
    app.run()
