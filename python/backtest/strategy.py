""" Strategy to be backtested. """

import backtrader as bt


# Create a Strategy
class TestStrategy(bt.Strategy):
    """ Base class to be subclassed for user defined strategies. """

    def __init__(self):

        # Keep a reference to the "close" line in the data[0] dataseries
        self.data_close = self.datas[0].close

        # To keep track of pending orders
        self.order = None

        self.bar_executed = 0

    def log(self, txt, dt=None):
        """ Logging function for this strategy. """

        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        """ Receives an order whenever there has been a change in one. """

        if order.status in [order.Submitted, order.Accepted]:
            # An active Buy/Sell order has been submitted/accepted - Nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'Buy executed @ {order.executed.price}')
            elif order.issell():
                self.log(f'Sell executed @  {order.executed.price}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset orders
        self.order = None

    def next(self):
        """
        This method will be called for all remaining data points when
        the minimum period for all datas/indicators have been meet.
        """

        self.log(f'Close:  {self.data_close[0]}')

        # check for open orders
        if self.order:
            return

        if not self.position:
            if self.data_close[0] < self.data_close[-3]:
                if self.data_close[-1] < self.data_close[-4]:

                    self.log(f'Buy submitted @ {self.data_close[0]}')

                    # keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:
            if self.data_close[0] > self.data_close[-5]:
                self.log(f'Sell submitted @ {self.data_close[0]}')

                # keep track of the created order to avoid a 2nd order
                self.order = self.sell()

