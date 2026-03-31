import threading
import time

import ib_app
from market_data.market_data_service import MarketDataService
from strategy.mean_reversion_strategy import MeanReversionStrategy
from backtesting.portfolio import Portfolio
from backtesting.engine import BacktestEngine
from utils.connection_constants import BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, LIVE_ENGINE_CLIENT_ID


def run_loop(app):
    app.run()


def wait_for_connection(app, timeout=10):
    """
    Block until nextValidId is received from TWS, confirming the connection
    is live. Raises RuntimeError if TWS does not respond within `timeout` seconds.
    This prevents the script from charging ahead on a dead socket.
    """
    start = time.time()
    while app.nextOrderId is None:
        if time.time() - start > timeout:
            raise RuntimeError(
                "Timed out waiting for TWS connection. "
                "Check that 'Enable ActiveX and Socket Clients' is enabled in "
                "TWS under Edit -> Global Configuration -> API -> Settings, "
                f"and that the socket port matches {BROKER_CONNECTION_PORT}."
            )
        time.sleep(0.1)


def main():
    app = ib_app.IBApp()
    app.connect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, clientId=LIVE_ENGINE_CLIENT_ID)

    thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    thread.start()

    wait_for_connection(app)

    mds = MarketDataService(app)

    df = mds.get_daily_bars("SPY")

    strategy = MeanReversionStrategy(window=20, spread_multiplier=0.5, max_position=50, order_size=10)
    portfolio = Portfolio(starting_cash=10000)

    engine = BacktestEngine(df, strategy, portfolio)

    equity_curve = engine.run()

    print("\nFinal Portfolio Value:", equity_curve[-1])
    print("Starting Portfolio Value: 10000")
    print("PnL:", round(equity_curve[-1] - 10000, 2))
    print("Total Trades:", len(portfolio.trade_log))
    print("Trade Log:")
    for trade in portfolio.trade_log:
        print(f"  {trade[0]:4s}  qty={trade[2]:>3}  price={trade[1]:.2f}")


if __name__ == "__main__":
    main()
