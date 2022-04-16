''' PaperStreet '''
import argparse
import os
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--file_name', type=str, required=True, help='The file name')
args = parser.parse_args()

os.chdir(os.path.expanduser('C:/Users/kylek/Desktop/'))

def extract(file_name):
    ''' Extract the OHLC from the market data captures.'''
    data = pd.read_csv(file_name, index_col=None, names=['timestamp', 'symbol', 'type', 'price'])

    data['timestamp'] = data['timestamp'].apply(
            lambda x: pd.Timestamp(x).strftime('%Y-%m-%d %H:%M:%S'))
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data = data.set_index('timestamp')

    open_px = data['price'].at_time('2022-03-28T08:30:10')
    high_px = data['price'].max()
    low_px = data['price'].min()
    close_px = data['price'].at_time('2022-03-28T15:00:00')

    return open_px, high_px, low_px, close_px
