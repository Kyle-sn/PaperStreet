import threading
import time

import ib_app
from contracts.contract_handler import ContractHandler
from market_data.market_data_service import MarketDataService
from orders import order_types
from orders.order_handler import connect_orders_handler, place_order
from positions.position_handler import request_account_updates
from strategy.mean_reversion_strategy import MeanReversionStrategy
from utils.log_config import setup_logger

logger = setup_logger(__name__)


def run_loop(app):
    app.run()


def initialize_ib_app():
    app = ib_app.IBApp()
    app.connect("127.0.0.1", 7497, clientId=1)

    thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    thread.start()
    time.sleep(2)

    return app


def initialize_services(app, account: str):
    mds = MarketDataService(app)
    order_app = connect_orders_handler()
    # Subscribe to account updates so updatePortfolio callbacks fire on the main
    # app instance. This keeps self.positions current and allows get_position()
    # to return broker-confirmed inventory to the strategy on each bar.
    request_account_updates(app, account)
    return mds, order_app


def initialize_strategy():
    strategy = MeanReversionStrategy(window=20, spread_multiplier=1.0, max_position=50, order_size=10)
    contract = ContractHandler.get_contract("SPY")
    return strategy, contract


def get_latest_bar(mds, symbol="SPY"):
    df = mds.get_daily_bars(symbol)
    latest_row = df.iloc[-1]
    return latest_row.to_dict()


def generate_signal(strategy, bar, app, symbol="SPY"):
    # Fetch broker-confirmed position from the app instance.
    # IBApp.get_position() reads from self.positions, which is populated
    # by updatePortfolio callbacks triggered by reqAccountUpdates.
    position = app.get_position(symbol)
    signal = strategy.on_bar(bar, position=position)
    logger.info(f"Bar processed|position={position}|signal={signal}")
    return signal


def execute_trade(signal, last_signal, order_app, contract):
    if signal is None:
        return last_signal

    action = signal["action"]
    quantity = signal["quantity"]

    # Suppress duplicate consecutive signals to avoid re-submitting the same
    # directional order on every bar when the strategy keeps firing the same action.
    if last_signal is not None and action == last_signal["action"]:
        logger.info(f"Suppressing duplicate {action} signal")
        return last_signal

    if action == "BUY":
        order = order_types.market_order("BUY", quantity)
        place_order(order_app, contract, order)

    elif action == "SELL":
        order = order_types.market_order("SELL", quantity)
        place_order(order_app, contract, order)

    return signal


def trading_loop(mds, strategy, order_app, contract, app, symbol="SPY"):
    logger.info("Starting live trading loop...")

    last_signal = None
    while True:
        try:
            bar = get_latest_bar(mds, symbol)
            signal = generate_signal(strategy, bar, app, symbol)
            last_signal = execute_trade(signal, last_signal, order_app, contract)
            time.sleep(60)
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            time.sleep(5)


def main():
    # Replace with your IBKR account number before running.
    account = "YOUR_ACCOUNT_NUMBER"
    symbol = "SPY"

    app = initialize_ib_app()
    mds, order_app = initialize_services(app, account)
    strategy, contract = initialize_strategy()

    trading_loop(mds, strategy, order_app, contract, app, symbol)


if __name__ == "__main__":
    main()
