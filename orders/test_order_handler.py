"""
test_order_handler.py

Unit tests for order_handler.py. No TWS connection required — app.placeOrder
is replaced with a MagicMock so no socket writes occur.

What this covers
----------------
1. wait_for_next_id returns immediately when nextOrderId is already set
2. wait_for_next_id raises TimeoutError when no ID arrives within the timeout
3. wait_for_next_id correctly waits for an ID that arrives after a short delay
4. place_order calls app.placeOrder exactly once
5. place_order passes the correct order ID from get_next_order_id
6. place_order passes the original contract and order objects through unchanged
7. Successive place_order calls use incrementing IDs

How to run
----------
    python orders/test_order_handler.py    (from project root)
"""

import sys
import os
import time
import traceback
import threading
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ibapi.contract import Contract

from ib_app import IBApp
from orders.order_handler import wait_for_next_id, place_order
from orders.order_types import market_order, limit_order


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


def _make_app(order_id=1):
    """IBApp with nextValidId fired and placeOrder mocked — no socket needed."""
    app = IBApp()
    app.nextValidId(order_id)
    app.placeOrder = MagicMock()
    return app


def _make_app_no_id():
    """IBApp with no nextValidId — simulates pre-connection state."""
    app = IBApp()
    app.placeOrder = MagicMock()
    return app


def _make_contract(symbol="SPY"):
    c = Contract()
    c.symbol = symbol
    c.secType = "STK"
    c.exchange = "SMART"
    c.currency = "USD"
    return c


# ---------------------------------------------------------------------------
# wait_for_next_id
# ---------------------------------------------------------------------------

def test_wait_for_next_id_returns_when_id_present():
    app = _make_app(42)
    result = wait_for_next_id(app, timeout=1)
    assert result == 42, f"Expected 42, got {result}"


def test_wait_for_next_id_raises_timeout_when_no_id():
    app = _make_app_no_id()
    try:
        wait_for_next_id(app, timeout=0.2)
        assert False, "Expected TimeoutError but nothing was raised"
    except TimeoutError:
        pass  # correct


def test_wait_for_next_id_waits_for_delayed_id():
    """ID arrives 100ms after wait starts — should still return it."""
    app = _make_app_no_id()

    def set_id_after_delay():
        time.sleep(0.1)
        app.nextValidId(99)

    t = threading.Thread(target=set_id_after_delay)
    t.start()
    result = wait_for_next_id(app, timeout=1.0)
    t.join()
    assert result == 99, f"Expected 99, got {result}"


# ---------------------------------------------------------------------------
# place_order
# ---------------------------------------------------------------------------

def test_place_order_calls_place_order_once():
    app = _make_app(1)
    place_order(app, _make_contract("SPY"), market_order("BUY", 10))
    app.placeOrder.assert_called_once()


def test_place_order_uses_next_order_id():
    app = _make_app(5)
    contract = _make_contract("SPY")
    order = market_order("BUY", 10)

    place_order(app, contract, order)

    order_id, passed_contract, passed_order = app.placeOrder.call_args[0]
    assert order_id == 5, f"Expected order ID 5, got {order_id}"


def test_place_order_passes_contract_and_order_unchanged():
    app = _make_app(1)
    contract = _make_contract("SPY")
    order = limit_order("SELL", 25, 500.00)

    place_order(app, contract, order)

    _, passed_contract, passed_order = app.placeOrder.call_args[0]
    assert passed_contract is contract, "Contract object should be passed through unchanged"
    assert passed_order is order, "Order object should be passed through unchanged"


def test_place_order_increments_id_on_successive_calls():
    app = _make_app(1)
    contract = _make_contract("SPY")

    place_order(app, contract, market_order("BUY", 10))
    place_order(app, contract, market_order("SELL", 10))

    calls = app.placeOrder.call_args_list
    assert len(calls) == 2
    first_id = calls[0][0][0]
    second_id = calls[1][0][0]
    assert second_id == first_id + 1, (
        f"Second order ID ({second_id}) should be first ({first_id}) + 1"
    )


def test_place_order_three_calls_unique_ids():
    app = _make_app(10)
    contract = _make_contract("SPY")

    for _ in range(3):
        place_order(app, contract, market_order("BUY", 1))

    ids = [call[0][0] for call in app.placeOrder.call_args_list]
    assert ids == [10, 11, 12], f"Expected [10, 11, 12], got {ids}"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    ("wait_for_next_id returns when ID already set",          test_wait_for_next_id_returns_when_id_present),
    ("wait_for_next_id raises TimeoutError when no ID",       test_wait_for_next_id_raises_timeout_when_no_id),
    ("wait_for_next_id waits for delayed ID",                 test_wait_for_next_id_waits_for_delayed_id),
    ("place_order calls placeOrder once",                     test_place_order_calls_place_order_once),
    ("place_order uses nextOrderId",                          test_place_order_uses_next_order_id),
    ("place_order passes contract and order unchanged",       test_place_order_passes_contract_and_order_unchanged),
    ("place_order increments ID on successive calls",         test_place_order_increments_id_on_successive_calls),
    ("place_order three calls produce sequential IDs",        test_place_order_three_calls_unique_ids),
]


def main():
    print("\n=== Order Handler Unit Tests ===\n")
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
