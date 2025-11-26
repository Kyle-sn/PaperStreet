package com.paperstreet.strategy;

import com.paperstreet.utils.LogHandler;
import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;

public class StrategyParameterReader {

    private static final LogHandler logHandler = new LogHandler();

    /**
     * Reads in a parameter when called and tries to find that parameter in strategy_parameters.json.
     *
     * @param param a parameter name in string format that should be a key found in strategy_parameters.json.
     * @return the relevant value associated with the key found in strategy_parameters.json
     */
    public static Object getParam(String param, int strategyId) {
        //TODO: rethink having this as an Object method
        try {
            FileReader reader = readStrategyParams();
            JSONObject jsonObject = new JSONObject(new JSONTokener(reader));
            JSONArray strategiesArray = jsonObject.getJSONArray("strategies");

            for (int i = 0; i < strategiesArray.length(); i++) {
                JSONObject strategy = strategiesArray.getJSONObject(i);
                if (strategy.getInt("strategy_id") == strategyId) {
                    JSONObject parametersJson = strategy.getJSONObject("parameters");

                    switch (param) {
                        case "symbol":
                            return getSymbol(param, parametersJson);
                        case "max_pos":
                            return getMaxPosition(param, parametersJson);
                        case "can_short":
                            return getCanShort(param, parametersJson);
                        case "signal_name":
                        case "fast_period":
                        case "slow_period":
                                return getSignalParameter(param, parametersJson);
                        default:
                            logHandler.logError("Invalid parameter being passed: " + param);
                            return null;
                    }
                }
            }
        } catch (FileNotFoundException e) {
            logHandler.logError("File not found: " + e.getMessage());
            return null;
        }
        return null;
    }

    public static List<Integer> getStrategyIds() {
        try {
            FileReader reader = readStrategyParams();
            JSONObject jsonObject = new JSONObject(new JSONTokener(reader));
            JSONArray strategiesArray = jsonObject.getJSONArray("strategies");

            List<Integer> strategyIds = new ArrayList<>();

            for (int i = 0; i < strategiesArray.length(); i++) {
                JSONObject strategy = strategiesArray.getJSONObject(i);
                int strategyId = strategy.getInt("strategy_id");
                strategyIds.add(strategyId);
            }
            return strategyIds;
        } catch (FileNotFoundException e) {
            logHandler.logError("File not found: " + e.getMessage());
            return null;
        }
    }

    private static int getMaxPosition(String param, JSONObject parameters) {
        return parameters.getInt(param);
    }

    private static String getSymbol(String param, JSONObject parameters) {
        return parameters.getString(param);
    }

    private static boolean getCanShort(String param, JSONObject parameters) {
        String canShort = parameters.getString(param);
        return Boolean.parseBoolean(canShort);
    }

    private static Object getSignalParameter(String param, JSONObject parameters) {
        if (parameters.has("signal")) {
            JSONObject signalJson = parameters.getJSONObject("signal");
            if (signalJson.has(param)) {
                return signalJson.get(param);
            } else {
                logHandler.logError("Signal parameter not found: " + param);
                return null;
            }
        } else {
            logHandler.logError("Signal object not found in parameters");
            return null;
        }
    }

    public static FileReader readStrategyParams() throws FileNotFoundException {
        return new FileReader(
                "C:\\Users\\kylek\\repos\\PaperStreet\\src\\main\\java\\com\\paperstreet\\strategy\\strategy_parameters.json");
    }
}
