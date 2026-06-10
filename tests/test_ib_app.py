"""
Pytest version of IBApp callback tests. No TWS connection required — EWrapper
callbacks are invoked directly to verify that state is updated correctly.
"""

import threading
from decimal import Decimal

import pytest
from ibapi.contract import Contract

from ib_app import IBApp


# ---------------------------------------------------------------------------
# nextValidId / order ID
# ---------------------------------------------------------------------------

def test_next_valid_id_sets_order_id():
    app = IBApp()
    assert app.nextOrderId is None
    app.nextValidId(42)
    assert app.nextOrderId == 42


def test_get_next_order_id_returns_and_increments(mock_app):
    first = mock_app.get_next_order_id()
    second = mock_app.get_next_order_id()
    assert first == 1
    assert second == 2


def test_get_next_order_id_thread_safe(mock_app):
    mock_app.nextOrderId = 1
    ids = []
    lock = threading.Lock()

    def grab():
        oid = mock_app.get_next_order_id()
        with lock:
            ids.append(oid)

    threads = [threading.Thread(target=grab) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(ids) == 20
    assert len(set(ids)) == 20, f"Duplicate IDs: {sorted(ids)}"


# ---------------------------------------------------------------------------
# updatePortfolio / get_position
# ---------------------------------------------------------------------------

def test_update_portfolio_stores_position(mock_app, make_contract):
    mock_app.updatePortfolio(make_contract("SPY"), Decimal("100"),
                             500.0, 50000.0, 490.0, 1000.0, 200.0, "U123")
    assert mock_app.get_position("SPY") == 100.0


def test_update_portfolio_zero_removes_symbol(mock_app, make_contract):
    mock_app.updatePortfolio(make_contract("SPY"), Decimal("100"),
                             500.0, 50000.0, 490.0, 1000.0, 200.0, "U123")
    mock_app.updatePortfolio(make_contract("SPY"), Decimal("0"),
                             500.0, 0.0, 490.0, 0.0, 0.0, "U123")
    assert mock_app.get_position("SPY") == 0.0
    assert "SPY" not in mock_app.positions


def test_get_position_unknown_symbol_returns_zero(mock_app):
    assert mock_app.get_position("AAPL") == 0.0


def test_update_portfolio_overwrites_with_latest(mock_app, make_contract):
    mock_app.updatePortfolio(make_contract("SPY"), Decimal("50"),
                             500.0, 25000.0, 490.0, 500.0, 100.0, "U123")
    mock_app.updatePortfolio(make_contract("SPY"), Decimal("75"),
                             502.0, 37650.0, 491.0, 825.0, 150.0, "U123")
    assert mock_app.get_position("SPY") == 75.0


def test_update_portfolio_tracks_multiple_symbols(mock_app, make_contract):
    mock_app.updatePortfolio(make_contract("SPY"), Decimal("100"),
                             500.0, 50000.0, 490.0, 1000.0, 200.0, "U123")
    mock_app.updatePortfolio(make_contract("QQQ"), Decimal("50"),
                             400.0, 20000.0, 395.0, 250.0, 50.0, "U123")
    assert mock_app.get_position("SPY") == 100.0
    assert mock_app.get_position("QQQ") == 50.0
    assert mock_app.get_position("IWM") == 0.0


# ---------------------------------------------------------------------------
# updateAccountValue
# ---------------------------------------------------------------------------

def test_update_account_value_cash_balance(mock_app):
    mock_app.updateAccountValue("TotalCashBalance", "100000.50", "USD", "U123")
    assert mock_app.get_current_cash_balance() == 100000.50


def test_update_account_value_maintenance_margin(mock_app):
    mock_app.updateAccountValue("MaintMarginReq", "5000.00", "USD", "U123")
    assert mock_app.get_current_maintenance_margin() == 5000.00


def test_update_account_value_initial_margin(mock_app):
    mock_app.updateAccountValue("InitMarginReq", "3000.00", "USD", "U123")
    assert mock_app.get_current_initial_margin() == 3000.00


def test_update_account_value_realized_pnl(mock_app):
    mock_app.updateAccountValue("RealizedPnL", "750.00", "USD", "U123")
    assert mock_app.get_realized_pnl() == 750.00


def test_update_account_value_unrealized_pnl(mock_app):
    mock_app.updateAccountValue("UnrealizedPnL", "1250.75", "USD", "U123")
    assert mock_app.get_unrealized_pnl() == 1250.75


def test_update_account_value_non_usd_cash_ignored(mock_app):
    mock_app.updateAccountValue("TotalCashBalance", "100000.00", "USD", "U123")
    mock_app.updateAccountValue("TotalCashBalance", "9999.00", "EUR", "U123")
    assert mock_app.get_current_cash_balance() == 100000.00


def test_account_values_start_as_none():
    app = IBApp()
    assert app.get_current_cash_balance() is None
    assert app.get_current_maintenance_margin() is None
    assert app.get_current_initial_margin() is None
    assert app.get_realized_pnl() is None
    assert app.get_unrealized_pnl() is None


# ---------------------------------------------------------------------------
# error callback
# ---------------------------------------------------------------------------

def test_error_info_codes_do_not_raise(mock_app):
    mock_app.error(-1, 2104, "Market data farm connection is OK:usfuture")
    mock_app.error(-1, 2106, "HMDS data farm connection is OK:ushmds")
    mock_app.error(-1, 2158, "Sec-def data farm connection is OK:secdefil")


def test_error_real_error_does_not_raise(mock_app):
    mock_app.error(1, 200, "No security definition has been found for the request")
    mock_app.error(1, 162, "Historical Market Data Service error message")
