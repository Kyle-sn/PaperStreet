"""
Tests for contracts/contract_handler.py.

ContractHandler builds ibapi.Contract objects for US equities. No IB
connection is required — the factory is pure construction logic.
"""

import pytest
from ibapi.contract import Contract

from contracts.contract_handler import ContractHandler


# ---------------------------------------------------------------------------
# get_contract field correctness
# ---------------------------------------------------------------------------

def test_get_contract_returns_contract_instance():
    assert isinstance(ContractHandler.get_contract("SPY"), Contract)


def test_get_contract_symbol():
    assert ContractHandler.get_contract("SPY").symbol == "SPY"


def test_get_contract_sec_type():
    assert ContractHandler.get_contract("SPY").secType == "STK"


def test_get_contract_exchange():
    assert ContractHandler.get_contract("SPY").exchange == "SMART"


def test_get_contract_currency():
    assert ContractHandler.get_contract("SPY").currency == "USD"


@pytest.mark.parametrize("symbol", ["SPY", "QQQ", "AAPL", "MSFT", "TSLA"])
def test_get_contract_uses_supplied_symbol(symbol):
    assert ContractHandler.get_contract(symbol).symbol == symbol


# ---------------------------------------------------------------------------
# Calling get_contract twice for same symbol returns equivalent objects
# ---------------------------------------------------------------------------

def test_get_contract_twice_equivalent_fields():
    c1 = ContractHandler.get_contract("SPY")
    c2 = ContractHandler.get_contract("SPY")
    assert c1.symbol == c2.symbol
    assert c1.secType == c2.secType
    assert c1.exchange == c2.exchange
    assert c1.currency == c2.currency


def test_get_contract_returns_new_object_each_call():
    # Without caching, each call produces a distinct object.
    # If an LRU cache is added later, update this test to reflect the new contract.
    c1 = ContractHandler.get_contract("SPY")
    c2 = ContractHandler.get_contract("SPY")
    assert c1 is not c2


# ---------------------------------------------------------------------------
# contract() and get_contract() are equivalent
# ---------------------------------------------------------------------------

def test_contract_and_get_contract_produce_same_fields():
    c1 = ContractHandler.contract("QQQ")
    c2 = ContractHandler.get_contract("QQQ")
    assert c1.symbol == c2.symbol
    assert c1.secType == c2.secType
    assert c1.exchange == c2.exchange
    assert c1.currency == c2.currency
