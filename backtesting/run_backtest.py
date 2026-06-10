from research.session import Session
from strategy.registry import build_strategy
from backtesting.portfolio import Portfolio
from backtesting.engine import BacktestEngine

# Backtest configuration. Swap strategies by changing `name`/`params` only —
# no imports or code changes. `name` must match a registered strategy.
SYMBOL = "SPY"
STRATEGY_NAME = "mean_reversion"
STRATEGY_PARAMS = {"window": 20, "spread_multiplier": 0.5, "max_position": 50, "order_size": 10}
STARTING_CASH = 10000


def main():
    with Session() as session:
        df = session.market_data.get_daily_bars(SYMBOL)

    strategy = build_strategy(STRATEGY_NAME, symbol=SYMBOL, params=STRATEGY_PARAMS)
    portfolio = Portfolio(starting_cash=STARTING_CASH)

    engine = BacktestEngine(df, strategy, portfolio)

    strategy.on_start()
    equity_curve = engine.run()
    strategy.on_stop()

    print("\nFinal Portfolio Value:", equity_curve[-1])
    print(f"Starting Portfolio Value: {STARTING_CASH}")
    print("PnL:", round(equity_curve[-1] - STARTING_CASH, 2))
    print("Total Trades:", len(portfolio.trade_log))
    print("Trade Log:")
    for trade in portfolio.trade_log:
        print(f"  {trade[0]:4s}  qty={trade[2]:>3}  price={trade[1]:.2f}")


if __name__ == "__main__":
    main()
