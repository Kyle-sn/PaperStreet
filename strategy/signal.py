"""
signal.py

The typed contract a strategy returns from `on_bar`.

A strategy never builds IBKR `Order` objects directly. It returns `OrderRequest`
objects, and the execution layer (orders/ in live, Portfolio in backtest)
translates them into fills or real IBKR calls. Keeping this a plain dataclass
means the same object flows unchanged through backtest and live, so a strategy
behaves identically in both.

`symbol` and `strategy` are populated automatically by BaseStrategy.buy()/sell()
from the strategy instance — concrete strategies should not set them by hand.
"""

from __future__ import annotations

from dataclasses import dataclass

# Allowed values, exposed so callers/tests can validate without re-typing them.
ACTIONS = ("BUY", "SELL")
ORDER_TYPES = ("MKT", "LMT")


@dataclass
class OrderRequest:
    """
    A single intended order produced by a strategy.

    Fields
    ------
    action : str
        'BUY' or 'SELL'. Matches the vocabulary used by orders/order_types.py
        and Portfolio, so it threads through to IBKR without remapping.
    quantity : float
        Number of shares/contracts. Always positive; direction is in `action`.
    order_type : str
        'MKT' or 'LMT'. Defaults to market.
    limit_price : float | None
        Required when order_type == 'LMT', ignored otherwise.
    tif : str
        Time in force. Defaults to 'DAY'.
    symbol : str
        Populated automatically from the strategy's symbol.
    strategy : str
        Populated automatically from the strategy's `name`, used to tag the
        order/execution rows in the database.
    """

    action: str
    quantity: float
    order_type: str = "MKT"
    limit_price: float | None = None
    tif: str = "DAY"
    symbol: str = ""
    strategy: str = ""

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise ValueError(f"action must be one of {ACTIONS}, got {self.action!r}")
        if self.order_type not in ORDER_TYPES:
            raise ValueError(f"order_type must be one of {ORDER_TYPES}, got {self.order_type!r}")
        if self.order_type == "LMT" and self.limit_price is None:
            raise ValueError("limit_price is required for LMT orders")
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive, got {self.quantity}")
