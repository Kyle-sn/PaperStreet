"""
Tests for orders/order_types.py factory functions.

All factories must return a configured ibapi.Order instance with the correct
fields set. No IB connection is required.
"""

import pytest
from ibapi.order import Order

from orders.order_types import (
    market_order,
    limit_order,
    stop_order,
    stop_limit_order,
    trailing_stop_order,
    trailing_stop_limit_order,
)


# ---------------------------------------------------------------------------
# Return type — all factories must return Order instances
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("factory, args", [
    (market_order, ("BUY", 10)),
    (limit_order, ("BUY", 10, 100.0)),
    (stop_order, ("SELL", 95.0, 10)),
    (stop_limit_order, ("SELL", 10, 94.0, 95.0)),
    (trailing_stop_order, ("SELL", 10, 5.0, 480.0)),
    (trailing_stop_limit_order, ("SELL", 10, 480.0, 0.50, 10.0)),
])
def test_all_factories_return_order_instance(factory, args):
    result = factory(*args)
    assert isinstance(result, Order)


# ---------------------------------------------------------------------------
# market_order
# ---------------------------------------------------------------------------

def test_market_order_action():
    assert market_order("BUY", 100).action == "BUY"


def test_market_order_type():
    assert market_order("BUY", 100).orderType == "MKT"


def test_market_order_quantity():
    assert market_order("BUY", 100).totalQuantity == 100


def test_market_order_tif():
    assert market_order("BUY", 100).tif == "DAY"


def test_market_order_sell():
    order = market_order("SELL", 50)
    assert order.action == "SELL"
    assert order.totalQuantity == 50


# ---------------------------------------------------------------------------
# limit_order
# ---------------------------------------------------------------------------

def test_limit_order_type():
    assert limit_order("BUY", 50, 150.00).orderType == "LMT"


def test_limit_order_price():
    assert limit_order("SELL", 50, 150.00).lmtPrice == 150.00


def test_limit_order_quantity():
    assert limit_order("BUY", 50, 150.00).totalQuantity == 50


def test_limit_order_tif():
    assert limit_order("BUY", 50, 150.00).tif == "DAY"


# ---------------------------------------------------------------------------
# stop_order
# ---------------------------------------------------------------------------

def test_stop_order_type():
    assert stop_order("SELL", 95.0, 10).orderType == "STP"


def test_stop_order_aux_price():
    assert stop_order("SELL", 95.0, 10).auxPrice == 95.0


def test_stop_order_quantity():
    assert stop_order("SELL", 95.0, 10).totalQuantity == 10


# ---------------------------------------------------------------------------
# stop_limit_order
# ---------------------------------------------------------------------------

def test_stop_limit_order_type():
    assert stop_limit_order("SELL", 10, 94.0, 95.0).orderType == "STP LMT"


def test_stop_limit_order_limit_price():
    assert stop_limit_order("SELL", 10, 94.0, 95.0).lmtPrice == 94.0


def test_stop_limit_order_stop_price():
    assert stop_limit_order("SELL", 10, 94.0, 95.0).auxPrice == 95.0


# ---------------------------------------------------------------------------
# trailing_stop_order
# ---------------------------------------------------------------------------

def test_trailing_stop_order_type():
    assert trailing_stop_order("SELL", 10, 5.0, 480.0).orderType == "TRAIL"


def test_trailing_stop_order_trailing_percent():
    assert trailing_stop_order("SELL", 10, 5.0, 480.0).trailingPercent == 5.0


def test_trailing_stop_order_trail_stop_price():
    assert trailing_stop_order("SELL", 10, 5.0, 480.0).trailStopPrice == 480.0


def test_trailing_stop_order_quantity():
    assert trailing_stop_order("SELL", 10, 5.0, 480.0).totalQuantity == 10


def test_trailing_stop_order_tif():
    assert trailing_stop_order("SELL", 10, 5.0, 480.0).tif == "DAY"


# ---------------------------------------------------------------------------
# trailing_stop_limit_order
# ---------------------------------------------------------------------------

def test_trailing_stop_limit_order_type():
    assert trailing_stop_limit_order("SELL", 10, 480.0, 0.50, 10.0).orderType == "TRAIL LIMIT"


def test_trailing_stop_limit_trail_stop_price():
    assert trailing_stop_limit_order("SELL", 10, 480.0, 0.50, 10.0).trailStopPrice == 480.0


def test_trailing_stop_limit_lmt_price_offset():
    assert trailing_stop_limit_order("SELL", 10, 480.0, 0.50, 10.0).lmtPriceOffset == 0.50


def test_trailing_stop_limit_aux_price_is_trailing_amount():
    # auxPrice holds the trailing amount for TRAIL LIMIT orders
    assert trailing_stop_limit_order("SELL", 10, 480.0, 0.50, 10.0).auxPrice == 10.0


# ---------------------------------------------------------------------------
# Negative quantity — documents current (unvalidated) behavior
# ---------------------------------------------------------------------------

def test_market_order_negative_quantity_not_rejected():
    # Currently no validation: negative qty is accepted as-is.
    # This test documents the gap and will fail once validation is added.
    order = market_order("BUY", -5)
    assert order.totalQuantity == -5


def test_limit_order_negative_quantity_not_rejected():
    order = limit_order("SELL", -10, 100.0)
    assert order.totalQuantity == -10
