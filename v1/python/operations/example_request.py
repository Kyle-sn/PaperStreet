import json
import requests


def run():
    url_base = 'https://api.stlouisfed.org/fred/series/observations?'

    # On almost all URLs, the default real-time period is today.
    # The real-time period marks when facts were true or when
    # information was known until it changed. Economic data sources,
    # releases, series, and observations are all assigned a real-time
    # period. Sources, releases, and series can change their names,
    # and observation data values can be revised.
    url_params = {
        'series_id': 'SP500',
        'file_type': 'json',
        'realtime_start': '2024-08-04',
        'realtime_end': '2024-08-04',
        'api_key': '48364fda9bc48ee78d182b9b58bee35b'
    }

    test_response = requests.get(url_base, params=url_params)

    if test_response.status_code != 200:
        raise Exception(
            f'Authentication error: status code {test_response.status_code}, reason: {test_response.reason}')

    content = json.loads(test_response.content)

    for entry in content['observations']:
        print(entry['date'], entry['value'])


if __name__ == "__main__":
    run()
