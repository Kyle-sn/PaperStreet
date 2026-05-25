"""
Tests for orders/order_handler.py. No TWS connection required — app.placeOrder
is replaced with a MagicMock so no socket writes occur.
"""

import threading
import time

import pytest
from unittest.mock import MagicMock
from ibapi.contract import Contract

from ib_app import IBApp
from orders.order_handler import wait_for_next_id, place_order
from orders.order_types import market_order, limit_order


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app_with_id():
    """IBApp with nextValidId fired at 1 and placeOrder mocked."""
    app = IBApp()
    app.nextValidId(1)
    app.placeOrder = MagicMock()
    return app


@pytest.fixture
def app_no_id():
    """IBApp with no nextValidId — simulates pre-connection state."""
    app = IBApp()
    app.placeOrder = MagicMock()
    return app


@pytest.fixture
def spy_contract():
    c = Contract()
    c.symbol = "SPY"
    c.secType = "STK"
    c.exchange = "SMART"
    c.currency = "USD"
    return c


# ---------------------------------------------------------------------------
# wait_for_next_id
# ---------------------------------------------------------------------------

def test_wait_for_next_id_returns_when_id_already_set(app_with_id):
    result = wait_for_next_id(app_with_id, timeout=1)
    assert result == 1


def test_wait_for_next_id_raises_timeout_when_no_id(app_no_id):
    with pytest.raises(TimeoutError):
        wait_for_next_id(app_no_id, timeout=0.2)


def test_wait_for_next_id_waits_for_delayed_id(app_no_id):
    """ID arrives 100 ms after the wait starts — should still be returned."""
    def set_id_after_delay():
        time.sleep(0.1)
        app_no_id.nextValidId(99)

    t = threading.Thread(target=set_id_after_delay)
    t.start()
    result = wait_for_next_id(app_no_id, timeout=1.0)
    t.join()
    assert result == 99


# ---------------------------------------------------------------------------
# place_order
# ---------------------------------------------------------------------------

def test_place_order_calls_place_order_once(app_with_id, spy_contract):
    place_order(app_with_id, spy_contract, market_order("BUY", 10))
    app_with_id.placeOrder.assert_called_once()


def test_place_order_uses_correct_order_id(spy_contract):
    app = IBApp()
    app.nextValidId(5)
    app.placeOrder = MagicMock()

    place_order(app, spy_contract, market_order("BUY", 10))

    order_id, _, _ = app.placeOrder.call_args[0]
    assert order_id == 5


def test_place_order_passes_contract_and_order_unchanged(app_with_id, spy_contract):
    order = limit_order("SELL", 25, 500.00)
    place_order(app_with_id, spy_contract, order)

    _, passed_contract, passed_order = app_with_id.placeOrder.call_args[0]
    assert passed_contract is spy_contract
    assert passed_order is order


def test_place_order_increments_id_on_successive_calls(app_with_id, spy_contract):
    place_order(app_with_id, spy_contract, market_order("BUY", 10))
    place_order(app_with_id, spy_contract, market_order("SELL", 10))

    calls = app_with_id.placeOrder.call_args_list
    first_id = calls[0][0][0]
    second_id = calls[1][0][0]
    assert second_id == first_id + 1


def test_place_order_three_calls_produce_sequential_ids(spy_contract):
    app = IBApp()
    app.nextValidId(10)
    app.placeOrder = MagicMock()

    for _ in range(3):
        place_order(app, spy_contract, market_order("BUY", 1))

    ids = [call[0][0] for call in app.placeOrder.call_args_list]
    assert ids == [10, 11, 12]


# ---------------------------------------------------------------------------
# orderStatus callback
# ---------------------------------------------------------------------------

def test_order_status_filled_does_not_raise(mock_app):
    # orderStatus currently only logs; verify it never raises
    from decimal import Decimal
    mock_app.orderStatus(
        order_id=1,
        status="Filled",
        filled=Decimal("100"),
        remaining=Decimal("0"),
        avg_fill_price=500.0,
        perm_id=12345,
        parent_id=0,
        last_fill_price=500.0,
        client_id=0,
        why_held="",
        mkt_cap_price=0.0,
    )
