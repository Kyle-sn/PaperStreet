#!/usr/bin/python3

import os
import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--historical_file', type=str, required=True, help='File to append a row to')
parser.add_argument('--new_file', type=str, required=True, help='File with the data to append')
parser.add_argument('--data_type', type=str, required=True, help='Type of market data to use')
args = parser.parse_args()

os.chdir(os.path.expanduser('C:/Users/kylek/Desktop/data/'))

def append_csv_as_row(historical_file, new_file, data_type):
    '''
    After OHLC data is downloaded, this script will append the new OHLC value to the
    respective historical dataset.
    '''

    historical_data = pd.read_csv(historical_file, header=None)
    new_data = pd.read_csv(new_file, header=None)

    new_row = new_data.loc[new_data[2] == data_type]
    historical_data = historical_data.append(new_row)
    historical_data.to_csv(historical_file, header=False, index=False)

    print(f'Appended data from {new_file} to {historical_file}')

append_csv_as_row(args.historical_file, args.new_file, args.data_type)
