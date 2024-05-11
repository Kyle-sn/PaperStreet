package com.paperstreet.strategy;

import com.paperstreet.utils.LogHandler;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.FileNotFoundException;
import java.io.FileReader;

public class StrategyParameterReader {

    private static final LogHandler logHandler = new LogHandler();

    /**
     * Reads in a parameter when called and tries to find that parameter in strategy_parameters.json.
     *
     * @param param a parameter name in string format that should be a key found in strategy_parameters.json.
     * @return the relevant value associated with the key found in strategy_parameters.json
     */
    public static Object getParam(String param) {
        //TODO: rethink having this as an Object method
        try {
            FileReader reader = readStrategyParams();
            JSONObject jsonObject = new JSONObject(new JSONTokener(reader));
            JSONObject parametersJson = jsonObject.getJSONObject("parameters");

            switch (param) {
                case "symbol":
                    return getSymbol(param, parametersJson);
                case "max_pos":
                    return getMaxPosition(param, parametersJson);
                case "can_short":
                    return getCanShort(param, parametersJson);
                default:
                    logHandler.logError("Invalid parameter being passed: " + param);
                    return null;
            }
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

    public static FileReader readStrategyParams() throws FileNotFoundException {
        return new FileReader(
                "C:\\Users\\kylek\\repos\\PaperStreet\\src\\main\\java\\com\\paperstreet\\strategy\\strategy_parameters.json");
    }
}
