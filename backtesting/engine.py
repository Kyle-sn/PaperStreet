"""
engine.py

Backtest engine for running trading strategies on historical market data.

Responsibilities
----------------
- Iterate over historical market data (bars)
- Feed each bar into the strategy
- Process any signals returned by the strategy in the portfolio
- Track portfolio equity over time
- Return results for analysis (equity curve, trade log, etc.)

Assumptions / Limitations
-------------------------
- Trades are executed at the bar's closing price
- No slippage, latency, or transaction costs
- Strategies are assumed to generate signals in the correct format
- Portfolio state (cash, position) is handled by Portfolio class
- This engine handles only a single asset at a time
"""

import pandas as pd
from backtesting.portfolio import Portfolio
from strategy.base_strategy import BaseStrategy


class BacktestEngine:
    """
    Core backtesting engine.

    Attributes
    ----------
    data : pandas.DataFrame
        Historical market data. Each row is one bar.
        Required columns:
        - "datetime"
        - "open"
        - "high"
        - "low"
        - "close"
        - "volume"

    strategy : BaseStrategy
        An instance of a trading strategy that implements `on_bar`.

    portfolio : Portfolio
        The portfolio object that handles cash, positions, and trade execution.

    Methods
    -------
    run():
        Executes the backtest and returns the equity curve.
    """

    def __init__(self, data: pd.DataFrame, strategy: BaseStrategy, portfolio: Portfolio):
        """
        Initialize the backtest engine.

        Parameters
        ----------
        data : pandas.DataFrame
            Historical market data for the backtest.

        strategy : BaseStrategy
            Strategy instance that will generate signals.

        portfolio : Portfolio
            Portfolio instance to track positions and cash.
        """
        self.data = data
        self.strategy = strategy
        self.portfolio = portfolio

    def run(self) -> list[float]:
        """
        Execute the backtest.

        Steps
        -----
        1. Iterate over each bar in chronological order.
        2. Pass the bar to the strategy's `on_bar` method.
        3. If a signal is returned, pass it to the portfolio to update state.
        4. Compute total portfolio value (cash + position * price) at each step.
        5. Store equity values to generate an equity curve.

        Returns
        -------
        list[float]
            A list of portfolio values (equity curve) over time.

        Notes
        -----
        - Assumes `data` is sorted chronologically (oldest first)
        - Equity is mark-to-market at the close of each bar
        - Signal and portfolio processing occurs in the order: Strategy → Portfolio → Equity Calculation
        """
        equity_curve = []

        for _, row in self.data.iterrows():
            # Convert pandas row to dict for strategy consumption
            bar = row.to_dict()

            # Generate signal from strategy.
            # Portfolio position is passed in so inventory-aware strategies
            # (e.g. MeanReversionStrategy) can gate signals against current holdings
            # without maintaining their own internal position counter.
            signal = self.strategy.on_bar(bar, position=self.portfolio.position)

            # Update portfolio with signal
            self.portfolio.process_signal(signal, bar)

            # Calculate total equity
            equity = self.portfolio.get_value(bar["close"])
            equity_curve.append(equity)

        return equity_curve
