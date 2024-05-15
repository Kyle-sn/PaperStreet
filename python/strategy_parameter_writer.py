import json


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
    # TODO: eventually get the hardcoded information from the research workflow
    strategy_id = 1234 # TODO: dynamically assign a strategy ID
    symbol = "QQQ"
    max_pos = 10
    can_short = False

    params = {
        "strategy_id": strategy_id,
        "parameters": {
            "symbol": symbol,
            "max_pos": max_pos,
            "can_short": can_short
        }
    }

    return json.dumps(params)

