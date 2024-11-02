import json
import requests
import pandas as pd
import mysql.connector
import os


def process_data():
    data = get_data()
    json_file_path = "/home/kyle/data/economic_calendar/test.json"
    csv_file_path = "/home/kyle/data/economic_calendar/test.csv"

    with open(json_file_path, 'w') as file:
        json.dump(data["release_dates"], file)

    df = pd.read_json(json_file_path)
    df.to_csv(csv_file_path, index=False)

    insert_data_to_db(csv_file_path)


def get_data():
    # get release dates for all releases of economic data.
    url_base = 'https://api.stlouisfed.org/fred/releases/dates?'

    # keeping the realtime start/end dates as the latest date will make it so that
    # the csv being written only has that data. Downstream this allows for only the
    # latest day's data to be inserted into the db.
    url_params = {
        'file_type': 'json',
        'realtime_start': '2024-11-01',
        'realtime_end': '2024-11-01',
        'api_key': '48364fda9bc48ee78d182b9b58bee35b',
        'include_release_dates_with_no_data': 'true',
    }

    response = requests.get(url_base, params=url_params)

    if response.status_code != 200:
        raise Exception(
            f'Authentication error: status code {response.status_code}, reason: {response.reason}')

    return json.loads(response.content)


def insert_data_to_db(csv_file_path):
    data = pd.read_csv(csv_file_path)
    # convert the 'release_last_updated' column to DATE format (YYYY-MM-DD)
    data['release_last_updated'] = pd.to_datetime(data['release_last_updated']).dt.date
    
    # create a new concatenated column to serve as the primary key in the db
    data['id'] = data['release_id'].astype(str) + '.' + data['date'].astype(str)
    # move the new id column to the front
    data = data[['id'] + [col for col in data.columns if col != 'id']] 
    print(data) 
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    
    connection = mysql.connector.connect(
        host="localhost",
        user=db_user,
        password=db_password,
        database="my_database"
    )

    cursor = connection.cursor()

    table_name = "economic_releases"
    columns = ", ".join(data.columns) # assumes csv columns match db columns
    placeholders = ", ".join(["%s"] * len(data.columns))
    sql_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    for index, row in data.iterrows():
        values = tuple(row)  # convert row to tuple for insertion
        cursor.execute(sql_query, values)

    connection.commit()

    cursor.close()
    connection.close()


if __name__ == "__main__":
    process_data()
