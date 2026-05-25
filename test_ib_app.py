"""
test_ib_app.py

Unit tests for IBApp callbacks. No TWS connection required — EWrapper
callbacks are invoked directly to verify that state is updated correctly.

What this covers
----------------
 1. nextValidId sets nextOrderId
 2. get_next_order_id returns current ID and increments
 3. get_next_order_id is thread-safe under concurrent access
 4. updatePortfolio stores a position by symbol
 5. updatePortfolio with zero position removes the symbol from the dict
 6. get_position returns 0.0 for an unknown symbol (no KeyError)
 7. updatePortfolio overwrites with the latest values on repeat callbacks
 8. updatePortfolio tracks multiple symbols independently
 9. updateAccountValue stores cash balance
10. updateAccountValue stores maintenance margin
11. updateAccountValue stores unrealized PnL
12. updateAccountValue ignores non-USD cash entries
13. Account values start as None before any callbacks fire
14. error callback with IB info codes does not raise
15. error callback with a real error does not raise

How to run
----------
    python test_ib_app.py          (from project root)
"""

import traceback
import threading
from decimal import Decimal

from ibapi.contract import Contract

from ib_app import IBApp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_test(name, fn):
    try:
        fn()
        print(f"  PASS  {name}")
        return True
    except AssertionError as e:
        print(f"  FAIL  {name}")
        print(f"        AssertionError: {e}")
        return False
    except Exception:
        print(f"  FAIL  {name}")
        traceback.print_exc()
        return False


def _make_app():
    """IBApp with nextValidId already fired — simulates post-connect state."""
    app = IBApp()
    app.nextValidId(1)
    return app


def _make_contract(symbol="SPY"):
    c = Contract()
    c.symbol = symbol
    c.secType = "STK"
    c.exchange = "SMART"
    c.currency = "USD"
    return c


# ---------------------------------------------------------------------------
# nextValidId / order ID
# ---------------------------------------------------------------------------

def test_next_valid_id_sets_order_id():
    app = IBApp()
    assert app.nextOrderId is None
    app.nextValidId(42)
    assert app.nextOrderId == 42, f"Expected 42, got {app.nextOrderId}"


def test_get_next_order_id_returns_and_increments():
    app = _make_app()  # nextOrderId = 1
    first = app.get_next_order_id()
    second = app.get_next_order_id()
    assert first == 1, f"Expected 1, got {first}"
    assert second == 2, f"Expected 2, got {second}"


def test_get_next_order_id_thread_safe():
    app = _make_app()
    app.nextOrderId = 1
    ids = []
    lock = threading.Lock()

    def grab():
        oid = app.get_next_order_id()
        with lock:
            ids.append(oid)

    threads = [threading.Thread(target=grab) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(ids) == 20, f"Expected 20 IDs, got {len(ids)}"
    assert len(set(ids)) == 20, f"Duplicate IDs detected: {sorted(ids)}"


# ---------------------------------------------------------------------------
# updatePortfolio / get_position
# ---------------------------------------------------------------------------

def test_update_portfolio_stores_position():
    app = _make_app()
    app.updatePortfolio(_make_contract("SPY"), Decimal("100"),
                        500.0, 50000.0, 490.0, 1000.0, 200.0, "U123")
    assert app.get_position("SPY") == 100.0


def test_update_portfolio_zero_removes_symbol():
    app = _make_app()
    app.updatePortfolio(_make_contract("SPY"), Decimal("100"),
                        500.0, 50000.0, 490.0, 1000.0, 200.0, "U123")
    assert app.get_position("SPY") == 100.0

    app.updatePortfolio(_make_contract("SPY"), Decimal("0"),
                        500.0, 0.0, 490.0, 0.0, 0.0, "U123")
    assert app.get_position("SPY") == 0.0, "Closed position should return 0.0"
    assert "SPY" not in app.positions, "Closed position should be removed from dict"


def test_get_position_unknown_symbol_returns_zero():
    app = _make_app()
    assert app.get_position("AAPL") == 0.0


def test_update_portfolio_overwrites_with_latest():
    app = _make_app()
    app.updatePortfolio(_make_contract("SPY"), Decimal("50"),
                        500.0, 25000.0, 490.0, 500.0, 100.0, "U123")
    app.updatePortfolio(_make_contract("SPY"), Decimal("75"),
                        502.0, 37650.0, 491.0, 825.0, 150.0, "U123")
    assert app.get_position("SPY") == 75.0


def test_update_portfolio_tracks_multiple_symbols():
    app = _make_app()
    app.updatePortfolio(_make_contract("SPY"), Decimal("100"),
                        500.0, 50000.0, 490.0, 1000.0, 200.0, "U123")
    app.updatePortfolio(_make_contract("QQQ"), Decimal("50"),
                        400.0, 20000.0, 395.0, 250.0, 50.0, "U123")
    assert app.get_position("SPY") == 100.0
    assert app.get_position("QQQ") == 50.0
    assert app.get_position("IWM") == 0.0


# ---------------------------------------------------------------------------
# updateAccountValue
# ---------------------------------------------------------------------------

def test_update_account_value_cash_balance():
    app = _make_app()
    app.updateAccountValue("TotalCashBalance", "100000.50", "USD", "U123")
    assert app.get_current_cash_balance() == 100000.50


def test_update_account_value_maintenance_margin():
    app = _make_app()
    app.updateAccountValue("MaintMarginReq", "5000.00", "USD", "U123")
    assert app.get_current_maintenance_margin() == 5000.00


def test_update_account_value_unrealized_pnl():
    app = _make_app()
    app.updateAccountValue("UnrealizedPNL", "1250.75", "USD", "U123")
    assert app.get_unrealized_pnl() == 1250.75


def test_update_account_value_non_usd_cash_ignored():
    app = _make_app()
    app.updateAccountValue("TotalCashBalance", "100000.00", "USD", "U123")
    app.updateAccountValue("TotalCashBalance", "9999.00", "EUR", "U123")
    assert app.get_current_cash_balance() == 100000.00, (
        "Non-USD cash callback should not overwrite USD balance"
    )


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

def test_error_info_codes_do_not_raise():
    app = _make_app()
    # IB sends these as status notifications when farms connect — must not raise
    app.error(-1, 2104, "Market data farm connection is OK:usfuture")
    app.error(-1, 2106, "HMDS data farm connection is OK:ushmds")
    app.error(-1, 2158, "Sec-def data farm connection is OK:secdefil")


def test_error_real_error_does_not_raise():
    app = _make_app()
    # Real error — should log but never raise, so the caller doesn't crash
    app.error(1, 200, "No security definition has been found for the request")
    app.error(1, 162, "Historical Market Data Service error message")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    ("nextValidId sets nextOrderId",                         test_next_valid_id_sets_order_id),
    ("get_next_order_id returns and increments",             test_get_next_order_id_returns_and_increments),
    ("get_next_order_id is thread-safe",                     test_get_next_order_id_thread_safe),
    ("updatePortfolio stores position",                      test_update_portfolio_stores_position),
    ("updatePortfolio zero position removes symbol",         test_update_portfolio_zero_removes_symbol),
    ("get_position unknown symbol returns 0.0",              test_get_position_unknown_symbol_returns_zero),
    ("updatePortfolio overwrites with latest",               test_update_portfolio_overwrites_with_latest),
    ("updatePortfolio tracks multiple symbols",              test_update_portfolio_tracks_multiple_symbols),
    ("updateAccountValue cash balance",                      test_update_account_value_cash_balance),
    ("updateAccountValue maintenance margin",                test_update_account_value_maintenance_margin),
    ("updateAccountValue unrealized PnL",                    test_update_account_value_unrealized_pnl),
    ("updateAccountValue non-USD cash ignored",              test_update_account_value_non_usd_cash_ignored),
    ("account values start as None",                         test_account_values_start_as_none),
    ("error info codes do not raise",                        test_error_info_codes_do_not_raise),
    ("real error callback does not raise",                   test_error_real_error_does_not_raise),
]


def main():
    print("\n=== IBApp Callback Unit Tests ===\n")
    passed = 0
    failed = 0
    for name, fn in TESTS:
        if run_test(name, fn):
            passed += 1
        else:
            failed += 1
    print(f"\n{'=' * 38}")
    print(f"  {passed} passed  |  {failed} failed  |  {len(TESTS)} total")
    print(f"{'=' * 38}\n")


if __name__ == "__main__":
    main()
