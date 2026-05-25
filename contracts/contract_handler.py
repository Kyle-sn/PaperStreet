import functools

from ibapi.contract import Contract

from utils.connection_constants import CURRENCY, EXCHANGE, SECURITY_TYPE
from utils.log_config import setup_logger

logger = setup_logger(__name__)


class ContractHandler:
    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_contract(symbol: str) -> Contract:
        """
        Return an IBKR Contract for the given US equity symbol.

        Results are cached by symbol — repeated calls return the same object,
        so callers must not mutate the returned Contract.
        """
        contract = Contract()
        contract.symbol = symbol
        contract.secType = SECURITY_TYPE
        contract.exchange = EXCHANGE
        contract.currency = CURRENCY
        logger.info(f"Contract created for {symbol}")
        return contract
