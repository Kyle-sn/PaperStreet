from ibapi.contract import Contract
from v2.connection_constants import *


class ContractHandler:
    @staticmethod
    def contract(ticker: str) -> Contract:
        """
        Converts the provided symbol to a valid IBKR contract.
        The contract helps identify and route market data requests to the broker
        specifying the security type, exchange, and currency of US stocks.
        """
        contract = Contract()
        contract.symbol = ticker
        contract.secType = SECURITY_TYPE
        contract.exchange = EXCHANGE
        contract.currency = CURRENCY

        print(f"Contract created for {ticker}")
        return contract

    @staticmethod
    def get_contract(symbol: str) -> Contract:
        """
        Returns an IBKR contract for the provided symbol.
        """
        return ContractHandler.contract(symbol)
