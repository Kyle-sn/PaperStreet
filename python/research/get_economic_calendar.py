import json
import requests
import pandas as pd


def process_data():
    data = get_data()
    json_file_path = "C:\\Users\\kylek\\data\\economic_calendar\\test.json"
    csv_file_path = "C:\\Users\\kylek\\data\\economic_calendar\\test.csv"

    with open(json_file_path, 'w') as file:
        json.dump(data["release_dates"], file)

    df = pd.read_json(json_file_path)
    df.drop(['release_id', 'release_last_updated'], axis=1, inplace=True)
    df.to_csv(csv_file_path, index=False)


def get_data():
    # Get release dates for all releases of economic data.
    url_base = 'https://api.stlouisfed.org/fred/releases/dates?'

    url_params = {
        'file_type': 'json',
        'realtime_start': '2024-08-04',
        'realtime_end': '2024-08-31',
        'api_key': '48364fda9bc48ee78d182b9b58bee35b',
        'include_release_dates_with_no_data': 'true',
    }

    response = requests.get(url_base, params=url_params)

    if response.status_code != 200:
        raise Exception(
            f'Authentication error: status code {response.status_code}, reason: {response.reason}')

    return json.loads(response.content)


if __name__ == "__main__":
    process_data()
