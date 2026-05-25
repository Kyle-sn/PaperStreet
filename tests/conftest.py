import sys
import os

import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from ibapi.contract import Contract

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ib_app import IBApp


@pytest.fixture
def mock_app():
    """IBApp instance with mocked EClient so no real connection is needed."""
    app = IBApp()
    app.conn = MagicMock()
    app.nextValidId(1)
    return app


@pytest.fixture
def make_contract():
    def _make(symbol="SPY"):
        c = Contract()
        c.symbol = symbol
        c.secType = "STK"
        c.exchange = "SMART"
        c.currency = "USD"
        return c
    return _make
