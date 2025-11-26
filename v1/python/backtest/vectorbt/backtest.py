import vectorbt as vbt

backtest_args = {
    'symbol': 'QQQ',
    'start_date': '2019-01-01 UTC',
    'end_date': '2024-05-01 UTC',
    'fast_period': 10,
    'slow_period': 50,
    'direction': 'longonly',
    'size': 100
}


def run_backtest(symbol, start_date, end_date, fast_period, slow_period, direction, size):
    # get data to run backtest with
    price = vbt.YFData.download(symbol, start=start_date, end=end_date).get('Close')

    # build strategy and return its entries and exits
    entries, exits = build_ma_cross_strategy(price, fast_period, slow_period)

    # model a portfolio for performance measuring
    pf = vbt.Portfolio.from_signals(
        price, entries, exits,
        direction=direction,
        size=size,
        size_type='amount',  # fixed number of shares/contracts
        init_cash=5000,
        fixed_fees=5,
        freq='1D')

    fig = price.vbt.plot(trace_kwargs=dict(name='Close'))
    pf.positions.plot(close_trace_kwargs=dict(visible=False), fig=fig)
    fig.show()

    stats = pf.stats()
    print("Backtesting Stats:")
    print(stats)


def build_ma_cross_strategy(price, fast_period, slow_period):
    fast_ma = vbt.MA.run(price, fast_period)
    slow_ma = vbt.MA.run(price, slow_period)
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    return entries, exits


def get_backtest_params(**backtest_args):
    symbol = backtest_args.get('symbol')
    fast_period = backtest_args.get('fast_period')
    slow_period = backtest_args.get('slow_period')
    direction = backtest_args.get('direction')
    size = backtest_args.get('size')
    return symbol, fast_period, slow_period, direction, size


def promote_strategy():
    return get_backtest_params(**backtest_args)


run_backtest(**backtest_args)
