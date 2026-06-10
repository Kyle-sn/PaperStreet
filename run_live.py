import time

from contracts.contract_handler import ContractHandler
from orders import order_types
from orders.order_handler import connect_orders_handler, place_order
from research.session import Session
from strategy.registry import build_strategy
from utils.connection_constants import ACCOUNT_NUMBER, LIVE_ENGINE_CLIENT_ID
from utils.log_config import setup_logger

logger = setup_logger(__name__)

# Live configuration. Swap strategies by changing name/params/symbol only.
# `name` must match a registered strategy (see strategy.registry).
SYMBOL = "SPY"
STRATEGY_NAME = "mean_reversion"
STRATEGY_PARAMS = {"window": 3, "spread_multiplier": 1.0, "max_position": 50, "order_size": 10}


def initialize_strategy():
    strategy = build_strategy(STRATEGY_NAME, symbol=SYMBOL, params=STRATEGY_PARAMS)
    contract = ContractHandler.get_contract(SYMBOL)
    return strategy, contract


def get_latest_bar(session, symbol=SYMBOL):
    df = session.market_data.get_daily_bars(symbol)
    return df.iloc[-1].to_dict()


def generate_signal(strategy, bar, session, symbol=SYMBOL):
    position = session.get_position(symbol)
    signal = strategy.on_bar(bar, position=position)
    logger.info(f"Bar processed|position={position}|signal={signal}")
    return signal


def execute_trade(signal, last_signal, order_app, contract):
    if signal is None:
        return last_signal

    # Suppress duplicate consecutive signals to avoid re-submitting the same
    # directional order on every bar when the strategy keeps firing the same action.
    if last_signal is not None and signal.action == last_signal.action:
        logger.info(f"Suppressing duplicate {signal.action} signal")
        return last_signal

    order = order_types.order_from_request(signal)
    place_order(order_app, contract, order)
    return signal


def trading_loop(session, strategy, order_app, contract, symbol=SYMBOL):
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
    session = Session(account=ACCOUNT_NUMBER, client_id=LIVE_ENGINE_CLIENT_ID)
    order_app = connect_orders_handler()
    strategy, contract = initialize_strategy()
    strategy.on_start()

    try:
        trading_loop(session, strategy, order_app, contract, SYMBOL)
    finally:
        strategy.on_stop()
        session.disconnect()


if __name__ == "__main__":
    main()
