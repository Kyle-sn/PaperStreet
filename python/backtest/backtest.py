''' Basic backtesting module. '''

import os
import sys
import backtrader as bt
from strategy import TestStrategy

# Create a cerebro entity
cerebro = bt.Cerebro()

# Add a strategy
cerebro.addstrategy(TestStrategy)

modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
datapath = os.path.join(modpath, 'C:/Users/kylek/Downloads/QQQ.csv')

# Create a Data Feed
data = bt.feeds.YahooFinanceCSVData(dataname=datapath, reverse=False)

if __name__ == '__main__':

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(5000.0)

    # Set the commission
    #cerebro.broker.setcommission(commission=0.001)

    # Default position size
    #cerebro.addsizer(bt.sizers.SizerFix, stake=3)

    # Run Cerebro Engine
    start_portfolio_value = cerebro.broker.getvalue()
    cerebro.run()

    end_portfolio_value = cerebro.broker.getvalue()
    pnl = end_portfolio_value - start_portfolio_value

    # Print out the final result
    print(f'Final Portfolio Value: {cerebro.broker.getvalue()}')
    print(f'PnL: {pnl}')

    # Plot the result
    cerebro.plot()
    