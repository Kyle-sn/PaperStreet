''' Basic backtesting module. '''

import os
import sys
import backtrader as bt
from strategy import TestStrategy

class BackTest:
    ''' Class used to run a backtest on a specified strategy. '''

    def __init__(self, strategy):
        self.strategy = strategy

    def run(self):
        ''' Run backtest. '''

        cerebro = bt.Cerebro()

        cerebro.addstrategy(self.strategy)

        modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        datapath = os.path.join(modpath, 'C:/Users/kylek/Downloads/QQQ.csv')

        # Create a Data Feed
        data = bt.feeds.YahooFinanceCSVData(dataname=datapath, reverse=False)

        # Add the Data Feed to Cerebro
        cerebro.adddata(data)

        cerebro.broker.setcash(5000.0)
        cerebro.broker.setcommission(commission=0.001)

        start_portfolio_value = cerebro.broker.getvalue()

        # Run Cerebro Engine
        cerebro.run()

        end_portfolio_value = cerebro.broker.getvalue()
        pnl = end_portfolio_value - start_portfolio_value

        # Print out the final result
        print(f'Final Portfolio Value: {cerebro.broker.getvalue()}')
        print(f'PnL: {pnl}')

        # Plot the result
        cerebro.plot()

if __name__ == '__main__':

    backtest = BackTest(TestStrategy)
    backtest.run()
    