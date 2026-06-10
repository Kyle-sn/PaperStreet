"""
base_strategy.py

The contract every bar-driven strategy implements. It is the single interface
the backtest engine and the live loop both consume — anything that satisfies it
is plug-and-play in both, with no surrounding code changes.

A strategy is a pure signal generator:
1. Receives completed bars one at a time (on_bar)
2. Maintains its own internal state (indicators)
3. Returns OrderRequest objects (or None) — it never places orders itself

Scope
-----
One instance trades one symbol. To trade multiple symbols, run multiple
instances. This keeps per-strategy state trivial (no per-symbol bookkeeping)
and matches the mid-frequency design in docs/STRATEGY.md.

Lifecycle hooks (on_start/on_stop/on_fill) default to no-ops so a strategy
overrides only what it needs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from strategy.signal import OrderRequest


class BaseStrategy(ABC):
    """
    Abstract base class for bar-driven trading strategies.

    Concrete strategies must define a unique `name` (used for DB tagging and
    registry lookup) and implement `on_bar`.

    Attributes
    ----------
    name : str
        Unique identifier. Set by the @register_strategy decorator, or as a
        class attribute.
    symbol : str
        Symbol this instance trades. Set by the registry factory at build time;
        defaults to "" for directly-constructed instances.
    """

    name: str = ""
    symbol: str = ""

    @abstractmethod
    def on_bar(self, bar: dict, position: float = 0.0) -> OrderRequest | None:
        """
        Process a single completed bar and optionally return an order.

        Parameters
        ----------
        bar : dict
            One time step of market data. Keys: datetime, open, high, low,
            close, volume (see docs/DATA_MODEL.md).
        position : float
            Current net position in the traded symbol.
            - Live: pass session.get_position(symbol) (broker-confirmed).
            - Backtest: pass Portfolio.position.
            Defaults to 0.0. Passing position rather than self-tracking avoids
            inventory drift when a signal is rejected downstream.

        Returns
        -------
        OrderRequest | None
            An order to submit, or None for no action. Build it with
            self.buy()/self.sell() so symbol and strategy are tagged for you.
        """
        ...

    # ------------------------------------------------------------------
    # Order construction helpers (auto-tag symbol + strategy name)
    # ------------------------------------------------------------------

    def buy(self, quantity: float, order_type: str = "MKT",
            limit_price: float | None = None, tif: str = "DAY") -> OrderRequest:
        return OrderRequest(
            action="BUY", quantity=quantity, order_type=order_type,
            limit_price=limit_price, tif=tif, symbol=self.symbol, strategy=self.name,
        )

    def sell(self, quantity: float, order_type: str = "MKT",
             limit_price: float | None = None, tif: str = "DAY") -> OrderRequest:
        return OrderRequest(
            action="SELL", quantity=quantity, order_type=order_type,
            limit_price=limit_price, tif=tif, symbol=self.symbol, strategy=self.name,
        )

    # ------------------------------------------------------------------
    # Lifecycle hooks — override as needed; default to no-ops
    # ------------------------------------------------------------------

    def on_start(self) -> None:
        """Called once when the strategy starts. Load warm-up history here."""

    def on_stop(self) -> None:
        """Called once when the strategy stops. Clean up state here."""

    def on_fill(self, action: str, quantity: float, price: float) -> None:
        """Called when an execution for this strategy is confirmed."""
