import pandas as pd

from contracts.contract_handler import ContractHandler
from market_data.base import MarketDataProvider
from utils.connection_constants import HISTORICAL_DATA_REQUEST_ID


class IBKRMarketDataClient(MarketDataProvider):

    def __init__(self, ib_app):
        self.ib = ib_app

    def get_historical_data(self, symbol: str, duration: str = "1 M", bar_size: str = "1 day"):
        contract = ContractHandler.get_contract(symbol)

        req_id = HISTORICAL_DATA_REQUEST_ID

        # reset state
        self.ib.historical_data = []
        self.ib._historical_data_event.clear()

        self.ib.reqHistoricalData(
            reqId=req_id,
            contract=contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=1,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )

        self.ib._historical_data_event.wait(timeout=10)

        if not self.ib.historical_data:
            raise ValueError(f"No IBKR data returned for {symbol}")

        df = pd.DataFrame(self.ib.historical_data)

        return df
