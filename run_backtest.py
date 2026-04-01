from research.session import Session
from strategy.mean_reversion_strategy import MeanReversionStrategy
from backtesting.portfolio import Portfolio
from backtesting.engine import BacktestEngine


def main():
    with Session() as session:
        df = session.market_data.get_daily_bars("SPY")

    strategy = MeanReversionStrategy(window=20, spread_multiplier=0.5, max_position=50, order_size=10)
    portfolio = Portfolio(starting_cash=10000)

    engine = BacktestEngine(df, strategy, portfolio)

    equity_curve = engine.run()

    print("\nFinal Portfolio Value:", equity_curve[-1])
    print("Starting Portfolio Value: 10000")
    print("PnL:", round(equity_curve[-1] - 10000, 2))
    print("Total Trades:", len(portfolio.trade_log))
    print("Trade Log:")
    for trade in portfolio.trade_log:
        print(f"  {trade[0]:4s}  qty={trade[2]:>3}  price={trade[1]:.2f}")


if __name__ == "__main__":
    main()
