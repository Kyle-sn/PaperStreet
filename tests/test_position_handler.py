"""
Tests for positions/position_handler.py.

Covers the public API of position_handler without a live TWS connection.
Position tracking via updatePortfolio is tested through IBApp directly,
since that is where state lives.
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from ibapi.contract import Contract

from ib_app import IBApp
from positions.position_handler import (
    request_account_updates,
    request_account_summary,
    request_positions,
)


# ---------------------------------------------------------------------------
# request_account_updates
# ---------------------------------------------------------------------------

def test_request_account_updates_calls_req_with_subscribe_true():
    app = MagicMock(spec=IBApp)
    request_account_updates(app, "U123456")
    app.reqAccountUpdates.assert_called_once_with(True, "U123456")


def test_request_account_updates_passes_account_string():
    app = MagicMock(spec=IBApp)
    request_account_updates(app, "DU999999")
    _, account_arg = app.reqAccountUpdates.call_args[0]
    assert account_arg == "DU999999"


# ---------------------------------------------------------------------------
# request_positions / request_account_summary
# ---------------------------------------------------------------------------

def test_request_positions_calls_req_positions():
    app = MagicMock(spec=IBApp)
    request_positions(app)
    app.reqPositions.assert_called_once()


def test_request_account_summary_calls_req_summary():
    app = MagicMock(spec=IBApp)
    request_account_summary(app)
    app.reqAccountSummary.assert_called_once()


# ---------------------------------------------------------------------------
# Position state via updatePortfolio (integration with IBApp)
# ---------------------------------------------------------------------------

def test_get_position_after_update_portfolio(mock_app, make_contract):
    mock_app.updatePortfolio(make_contract("MSFT"), Decimal("200"),
                             300.0, 60000.0, 295.0, 1000.0, 200.0, "U123")
    assert mock_app.get_position("MSFT") == 200.0


def test_multiple_updates_for_same_symbol_keep_latest(mock_app, make_contract):
    mock_app.updatePortfolio(make_contract("AAPL"), Decimal("10"),
                             150.0, 1500.0, 145.0, 50.0, 10.0, "U123")
    mock_app.updatePortfolio(make_contract("AAPL"), Decimal("25"),
                             151.0, 3775.0, 146.0, 125.0, 25.0, "U123")
    assert mock_app.get_position("AAPL") == 25.0


def test_position_zero_on_close(mock_app, make_contract):
    mock_app.updatePortfolio(make_contract("TSLA"), Decimal("10"),
                             200.0, 2000.0, 195.0, 50.0, 10.0, "U123")
    assert mock_app.get_position("TSLA") == 10.0

    mock_app.updatePortfolio(make_contract("TSLA"), Decimal("0"),
                             200.0, 0.0, 195.0, 0.0, 0.0, "U123")
    assert mock_app.get_position("TSLA") == 0.0
    assert "TSLA" not in mock_app.positions
