from abc import ABC, abstractmethod
import pandas as pd


class MarketDataProvider(ABC):

    @abstractmethod
    def get_historical_data(self, symbol: str, duration: str, bar_size: str) -> pd.DataFrame:
        pass