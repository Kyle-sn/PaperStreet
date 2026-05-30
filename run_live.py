import time

from contracts.contract_handler import ContractHandler
from orders import order_types
from orders.order_handler import connect_orders_handler, place_order
from research.session import Session
from strategy.mean_reversion_strategy import MeanReversionStrategy
from utils.connection_constants import ACCOUNT_NUMBER, LIVE_ENGINE_CLIENT_ID
from utils.log_config import setup_logger

logger = setup_logger(__name__)


def initialize_strategy():
    strategy = MeanReversionStrategy(window=3, spread_multiplier=1.0, max_position=50, order_size=10)
    contract = ContractHandler.get_contract("SPY")
    return strategy, contract


def get_latest_bar(session, symbol="SPY"):
    df = session.market_data.get_daily_bars(symbol)
    return df.iloc[-1].to_dict()


def generate_signal(strategy, bar, session, symbol="SPY"):
    position = session.get_position(symbol)
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

    order = order_types.market_order(action, quantity)
    place_order(order_app, contract, order)
    return signal


def trading_loop(session, strategy, order_app, contract, symbol="SPY"):
    logger.info("Starting live trading loop...")

    last_signal = None
    while True:
        try:
            bar = get_latest_bar(session, symbol)
            signal = generate_signal(strategy, bar, session, symbol)
            last_signal = execute_trade(signal, last_signal, order_app, contract)
            time.sleep(60)
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            time.sleep(5)


def main():
    symbol = "SPY"

    session = Session(account=ACCOUNT_NUMBER, client_id=LIVE_ENGINE_CLIENT_ID)
    order_app = connect_orders_handler()
    strategy, contract = initialize_strategy()

    try:
        trading_loop(session, strategy, order_app, contract, symbol)
    finally:
        session.disconnect()


if __name__ == "__main__":
    main()
