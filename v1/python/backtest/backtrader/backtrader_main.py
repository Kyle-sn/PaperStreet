import backtrader as bt
import backtrader.analyzers as btanalyzers


class SmaCross(bt.SignalStrategy):
    params = dict(
        pfast=10,
        pslow=30
    )

    def __init__(self):
        # TODO: standardize parameters specifications here
        sma1 = bt.ind.SMA(period=self.p.pfast)
        sma2 = bt.ind.SMA(period=self.p.pslow)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)


# create engine instance
cerebro = bt.Cerebro()

# import data
# TODO: dynamically find and use the relevant data source
data = bt.feeds.YahooFinanceCSVData(dataname='C:\\Users\\kylek\\data\\market_data\\yahoo_finance\\QQQ_raw_test.csv')

# set up analyzer
# TODO: standardize the use and output of "Analyzers"
cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='mysharpe')

# TODO: customize what the output chart looks like by specifying Observers

# import strategy
cerebro.addstrategy(SmaCross)

cerebro.adddata(data)

results = cerebro.run()
backtest = results[0]
print('Sharpe Ratio:', backtest.analyzers.mysharpe.get_analysis())
cerebro.plot()
