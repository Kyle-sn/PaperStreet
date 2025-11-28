import time

from ibapi.account_summary_tags import AccountSummaryTags

from v2.ib_app import IBApp
from v2.connection_constants import *


def connect_position_handler():
    print("Starting IB connection...")
    app = IBApp()
    app.connect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, clientId=0)
    print("Connected. Entering event loop...")

    start = time.time()
    while (time.time() - start) < 1:  # wait up to 1 second
        if app.nextOrderId is not None:
            print("IBKR connection established!")
            break
        time.sleep(0.1)
    else:
        print("ERROR: Connection timed out. nextValidId not received.")
    return app


def request_account_summary(app):
    print("Requesting account summary")
    app.reqAccountSummary(1, "All", AccountSummaryTags.AllTags)


def request_account_updates(app, account):
    print("Requesting account updates")
    app.reqAccountUpdates(True, account)


def request_positions(app):
    print("Requesting positions")
    app.reqPositions()


if __name__ == "__main__":
    app = connect_position_handler()
    request_account_summary(app)
    request_account_updates(app, "DU5231415")
    request_positions(app)
    app.run()
