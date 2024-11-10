import argparse
import json
import os
from datetime import datetime
import mysql.connector
import requests
from db_utils import get_previous_value

parser = argparse.ArgumentParser()
parser.add_argument('--symbol', type=str, required=True, help='FRED data identifier')
args = parser.parse_args()


def process_data(symbol):
    current_date = datetime.now().strftime('%Y-%m-%d')
    data_set = get_data(symbol, current_date)
    insert_data_to_db(data_set, symbol)


# TODO: introduce polling to the api call and check if the release_last_updated for this symbol
#   has today's date. The polling should be to https://api.stlouisfed.org/fred/releases/dates? similar to
#   get_economic_releases. Once date is today's date, we then download the data via this script
def get_data(symbol, current_date):
    url_base = 'https://api.stlouisfed.org/fred/series/observations?'

    # On almost all URLs, the default real-time period is today.
    # The real-time period marks when facts were true or when
    # information was known until it changed. Economic data sources,
    # releases, series, and observations are all assigned a real-time
    # period. Sources, releases, and series can change their names,
    # and observation data values can be revised.
    url_params = {
        'series_id': symbol,
        'file_type': 'json',
        'realtime_start': current_date,
        'realtime_end': current_date,
        'api_key': '48364fda9bc48ee78d182b9b58bee35b'
    }

    response = requests.get(url_base, params=url_params)

    if response.status_code != 200:
        raise Exception(
            f'Authentication error: status code {response.status_code}, reason: {response.reason}')

    content = json.loads(response.content)
    entry = content['observations'][-1]  # get last value
    date = entry['date']
    value = entry['value']

    if not value:
        value = get_previous_value('fred_data', symbol, date)

    return {(date, value)}


def insert_data_to_db(data_set, symbol):
    date, value = next(iter(data_set))

    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')

    connection = mysql.connector.connect(
        host="localhost",
        user=db_user,
        password=db_password,
        database="my_database"
    )

    cursor = connection.cursor()

    table_name = "fred_data"
    id_value = f"{symbol}.{date}"
    sql_query = f"INSERT INTO {table_name} (id, date, symbol, value) VALUES (%s, %s, %s, %s)"

    cursor.execute(sql_query, (id_value, date, symbol, value))

    connection.commit()

    cursor.close()
    connection.close()


process_data(args.symbol)
