import threading
import time

import ib_app
from contracts.contract_handler import ContractHandler
from market_data.market_data_service import MarketDataService
from orders import order_types
from orders.order_handler import connect_orders_handler, place_order
from strategy.moving_average import MovingAverageStrategy
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


def initialize_services(app):
    mds = MarketDataService(app)
    order_app = connect_orders_handler()
    return mds, order_app


def initialize_strategy():
    strategy = MovingAverageStrategy(window=5)
    contract = ContractHandler.get_contract("SPY")
    return strategy, contract


def get_latest_bar(mds, symbol="SPY"):
    df = mds.get_daily_bars(symbol)
    latest_row = df.iloc[-1]
    return latest_row.to_dict()


def generate_signal(strategy, bar):
    signal = strategy.on_bar(bar)
    logger.info(f"Bar processed and signal received: {signal}")
    return signal


def execute_trade(signal, last_signal, order_app, contract):
    if signal is None or signal == last_signal:
        return last_signal

    if signal == "BUY":
        order = order_types.market_order("BUY", 1)
        place_order(order_app, contract, order)

    elif signal == "SELL":
        order = order_types.market_order("SELL", 1)
        place_order(order_app, contract, order)

    return signal


def trading_loop(mds, strategy, order_app, contract):
    logger.info("Starting live trading loop...")

    last_signal = None
    while True:
        try:
            bar = get_latest_bar(mds)
            signal = generate_signal(strategy, bar)
            last_signal = execute_trade(signal, last_signal, order_app, contract)
            time.sleep(60)
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            time.sleep(5)


def main():
    app = initialize_ib_app()
    mds, order_app = initialize_services(app)
    strategy, contract = initialize_strategy()

    trading_loop(mds, strategy, order_app, contract)


if __name__ == "__main__":
    main()