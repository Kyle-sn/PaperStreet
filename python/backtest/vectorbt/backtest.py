import vectorbt as vbt


def run_backtest(symbol, start_date, end_date, fast_period, slow_period):
    # get data to run backtest with
    price = vbt.YFData.download(symbol, start=start_date, end=end_date).get('Close')

    # build strategy and return its entries and exits
    entries, exits = build_ma_cross_strategy(price, fast_period, slow_period)

    # model a portfolio for performance measuring
    pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100, fees=0.005)

    #TODO: add more vectorbt logic here related to strategy analysis/optimization/etc.
    fig = price.vbt.plot(trace_kwargs=dict(name='Close'))
    pf.positions.plot(close_trace_kwargs=dict(visible=False), fig=fig)
    fig.show()

    print(pf.total_profit())


def build_ma_cross_strategy(price, fast_period, slow_period):
    #TODO: determine a max postiion to be used as a param
    #TODO: determine if the strategy is allowed to short. Adjust the backtesting logic
    # based on this parameter, i.e. if cant short, then make sure the backtest does not
    # do any shorting

    fast_ma = vbt.MA.run(price, fast_period)
    slow_ma = vbt.MA.run(price, slow_period)
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    return entries, exits


run_backtest(symbol='QQQ',
             start_date='2019-01-01 UTC',
             end_date='2024-05-01 UTC',
             fast_period=10,
             slow_period=50)
