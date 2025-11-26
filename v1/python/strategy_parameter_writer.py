import json

from v1.python.backtest.vectorbt.backtest import promote_strategy


def write_parameters():
    params_file_path = ("C:\\Users\\kylek\\repos\\PaperStreet\\src\\main\\java\\com"
                        "\\paperstreet\\strategy\\strategy_parameters.json")
    with open(params_file_path, "r+") as params_file:
        params_data = json.load(params_file)
        new_parameters = json.loads(get_parameters())
        params_data["strategies"].append(new_parameters)

        # move the file pointer to the beginning of the file
        params_file.seek(0)

        # write the updated data back to the file
        json.dump(params_data, params_file, indent=2)

        # truncate the file to the current size (in case the new data is smaller)
        params_file.truncate()


def get_parameters():
    symbol, ma_fast_period, ma_slow_period, direction, size = promote_strategy()

    strategy_id = 456
    signal = 'ma_cross'
    symbol = symbol
    max_pos = size
    if direction == 'longonly':
        can_short = "False"
    else:
        can_short = "True"

    params = {
        "strategy_id": strategy_id,
        "parameters": {
            "symbol": symbol,
            "max_pos": max_pos,
            "can_short": can_short,
            "signal": {
                "signal_name": signal,
                "fast_period": ma_fast_period,
                "slow_period": ma_slow_period
            }
        }
    }

    return json.dumps(params)


write_parameters()

#TODO: dynamically assign a strategy ID. Start from 1 and go up until an ID number isnt being used
# - read all strategies in param file
# - find the highest int value then increase by 1
