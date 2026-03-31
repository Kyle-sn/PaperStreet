from market_data.ibkr_client import IBKRMarketDataClient


class MarketDataService:

    def __init__(self, ib_app):
        self.provider = IBKRMarketDataClient(ib_app)

    def get_daily_bars(self, symbol: str):
        return self.provider.get_historical_data(
            symbol,
            duration="3 M",
            bar_size="1 day"
        )