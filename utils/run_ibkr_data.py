import threading
import time

import ib_app
from market_data.market_data_service import MarketDataService


def run_loop(app):
    app.run()


def main():
    app = ib_app.IBApp()

    app.connect("127.0.0.1", 7497, clientId=1)

    thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    thread.start()

    time.sleep(2)  # give time to connect

    mds = MarketDataService(app)

    df = mds.get_daily_bars("SPY")

    print("\n=== DATA ===")
    print(df.head())
    print(df.tail())


if __name__ == "__main__":
    main()