import threading
import time

import ib_app
from market_data.market_data_service import MarketDataService
from strategy.moving_average import MovingAverageStrategy
from backtesting.portfolio import Portfolio
from backtesting.engine import BacktestEngine


def run_loop(app):
    app.run()


def main():
    app = ib_app.IBApp()
    app.connect("127.0.0.1", 7497, clientId=1)

    thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    thread.start()

    time.sleep(2)

    mds = MarketDataService(app)

    df = mds.get_daily_bars("SPY")

    strategy = MovingAverageStrategy(window=5)
    portfolio = Portfolio(starting_cash=10000)

    engine = BacktestEngine(df, strategy, portfolio)

    equity_curve = engine.run()

    print("\nFinal Portfolio Value:", equity_curve[-1])
    print("Trades:", portfolio.trade_log)


if __name__ == "__main__":
    main()