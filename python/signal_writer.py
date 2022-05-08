import os
import argparse
import talib as ta
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--historical_data', type=str, required=True, help='Historical data file')
parser.add_argument('--fast', type=int, required=True, help='Number of days for fast SMA')
parser.add_argument('--slow', type=int, required=True, help='Number of days for slow SMA')
args = parser.parse_args()

os.chdir(os.path.expanduser('C:/Users/kylek/Desktop/data/'))

def write(historical_data, fast, slow):
    ''' Write signal based on analysis of historical data. '''

    data = pd.read_csv(historical_data, header=None)
    data.columns = ['time', 'symbol', 'data_type', 'value']
    data['slow_ma'] = data['value'].rolling(slow).mean()
    data['fast_ma'] = data['value'].rolling(fast).mean()
    
    data['signal'] = ''
    data.loc[data['slow_ma'] > data['fast_ma'], 'signal'] = 'sell'
    data.loc[data['slow_ma'] < data['fast_ma'], 'signal'] = 'buy'
    signal = data['signal'].iloc[-1]
    
    textfile = open("signal.csv", "w")
    a = textfile.write(signal)
    textfile.close()
    
write(args.historical_data, args.slow, args.fast)
