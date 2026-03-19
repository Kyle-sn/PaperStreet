"""
base_strategy.py

Defines the abstract interface for all trading strategies.

A strategy is responsible for:
1. Receiving market data (one bar at a time)
2. Maintaining any internal state (indicators, signals, etc.)
3. Returning trading signals based on that data

This file establishes the contract that all concrete strategies must follow
in order to integrate with the backtesting engine or live trading system.
"""

from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.

    All strategies must implement the `on_bar` method.

    The backtesting engine (and later live system) will call `on_bar`
    sequentially for each incoming data point (bar).
    """

    @abstractmethod
    def on_bar(self, bar: dict) -> dict | None:
        """
        Process a single bar of market data and optionally return a trading signal.

        Parameters
        ----------
        bar : dict
            A dictionary representing a single time step of market data.
            Expected format:
            {
                "datetime": str or datetime,
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float
            }

        Returns
        -------
        dict or None
            A signal dictionary if a trade action is generated, otherwise None.

            Expected signal format:
            {
                "action": "BUY" | "SELL",
                "quantity": int
            }

        Notes
        -----
        - This method is called once per bar in chronological order.
        - The strategy is responsible for maintaining its own internal state
          (e.g., moving averages, indicators, past prices).
        - Returning None means "no action".
        - The execution of the signal (fills, slippage, etc.) is handled
          by the portfolio or execution layer, NOT the strategy.

        Example
        -------
         signal = strategy.on_bar(bar)
         if signal:
             print(signal["action"], signal["quantity"])
        """
        pass
