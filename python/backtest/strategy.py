''' Strategy to be backtested. '''

import backtrader as bt

# Create a Stratey
class TestStrategy(bt.Strategy):
    ''' Base class to be subclassed for user defined strategies. '''

    # Moving average parameters
    params = (('pfast',2),('pslow',184),)

    def __init__(self):

        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

		# Order variable will contain ongoing order details/status
        self.order = None

        # Instantiate moving averages
        self.slow_sma = bt.indicators.MovingAverageSimple(self.datas[0], 
                        period=self.params.pslow)
        self.fast_sma = bt.indicators.MovingAverageSimple(self.datas[0], 
                        period=self.params.pfast)

        self.bar_executed = 0

    def log(self, txt, dt=None):
        ''' Logging function for this strategy. '''

        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def next(self):
        '''
        This method will be called for all remaining data points when
        the minimum period for all datas/indicators have been meet.
        '''

        # Check for open orders
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # We are not in the market, look for a signal to OPEN trades

            if self.fast_sma[0] > self.slow_sma[0]:
                self.log(f'BUY CREATED: {self.dataclose[0]:2f}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()
            elif self.fast_sma[0] < self.slow_sma[0]:
                self.log(f'SELL CREATED: {self.dataclose[0]}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
        else:
            # We are already in the market, look for a signal to CLOSE trades
            if len(self) >= (self.bar_executed + 3):
                self.log(f'CLOSE CREATE {self.dataclose[0]:2f}')
                self.order = self.close()

    def notify_order(self, order):
        ''' Receives an order whenever there has been a change in one. '''

        if order.status in [order.Submitted, order.Accepted]:
            # An active Buy/Sell order has been submitted/accepted - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: {order.executed.price}')
            elif order.issell():
                self.log(f'SELL EXECUTED: {order.executed.price}')
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset orders
        self.order = None
