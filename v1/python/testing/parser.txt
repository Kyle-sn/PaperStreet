import pandas as pd
import mysql.connector
import os


def main():
    csv_data = get_csv_data()
    db_data = get_db_data()

    # normalize headers by changing the csv data formats to match clipse data formats
    csv_data.rename(columns={
        'TimeStamp': 'time',
        'Underlying': 'underlying',
        'Feedcode': 'feedcode',
        'Volume': 'volume',
        'Price': 'price',
        'BS': 'buysell',
        'Kind': 'kind',
        'ExchangeTradeID': 'exchangetradeid',
    }, inplace=True)

    # drop unused columns
    csv_data.drop(columns=['Currency', 'Fee', 'Trade type'], inplace=True)
    db_data.drop(columns=['tradeid'], inplace=True)

    # normalize data types
    csv_data['volume'] = csv_data['volume'].astype(float)
    csv_data['exchangetradeid'] = csv_data['exchangetradeid'].astype(int)
    # changing a db_data data type here because I dont know how to work with the 'object' type
    db_data['exchangetradeid'] = db_data['exchangetradeid'].astype(int)

    # merge the two data sets on 'exchangetradeid'
    merged_df = pd.merge(csv_data, db_data, on='exchangetradeid', suffixes=('_csv', '_db'), how='outer')
    comparison_bool = (merged_df['time_csv'] == merged_df['time_db']) & \
                      (merged_df['underlying_csv'] == merged_df['underlying_db']) & \
                      (merged_df['feedcode_csv'] == merged_df['feedcode_db']) & \
                      (merged_df['volume_csv'] == merged_df['volume_db']) & \
                      (merged_df['price_csv'] == merged_df['price_db']) & \
                      (merged_df['buysell_csv'] == merged_df['buysell_db']) & \
                      (merged_df['kind_csv'] == merged_df['kind_db'])

    missing_trades = merged_df.loc[comparison_bool == False, 'exchangetradeid']
    print(missing_trades)

    # reconciliation
    exchange_trade_count = len(csv_data)
    eclipse_trade_count = len(db_data)
    # was not able to finish this in the allowed time
    exchange_trade_not_in_internal = ""
    internal_trade_not_in_exchange = ""

    with open('report.csv', 'w') as file:
        file.write(f'Exchange trades: {exchange_trade_count}\n')
        file.write(f'Eclipse trades: {eclipse_trade_count}\n')
        file.write(f'Trades found in exchange list but not in the internal list: {exchange_trade_not_in_internal}\n')
        file.write(f'Trades found in internal list but not in the exchange list: {internal_trade_not_in_exchange}\n')


def get_csv_data():
    csv_data = pd.read_csv("ExchangeTradeList.csv")
    return csv_data


def get_db_data():
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')

    connection = mysql.connector.connect(
        host="localhost",
        user=db_user,
        password=db_password,
        database="eclipse"
    )

    query = "SELECT * FROM trades"
    db_data = pd.read_sql(query, connection)

    connection.close()
    return db_data


main()
