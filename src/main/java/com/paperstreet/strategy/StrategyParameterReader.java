package com.paperstreet.strategy;

import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.FileNotFoundException;
import java.io.FileReader;

public class StrategyParameterReader {

    public static void main(String[] args) throws FileNotFoundException {
        getParam("can_short");
    }
    public static void getParam(String param) throws FileNotFoundException {
        try {
            FileReader reader = readStrategyParams();
            JSONObject jsonObject = new JSONObject(new JSONTokener(reader));
            JSONObject parametersJson = jsonObject.getJSONObject("parameters");

            switch (param) {
                case "symbol":
                    getSymbol(param, parametersJson);
                    break;
                case "max_pos":
                    getMaxPosition(param, parametersJson);
                    break;
                case "can_short":
                    getCanShort(param, parametersJson);
                    break;
            }
        } catch (FileNotFoundException e) {
            System.err.println("File not found: " + e.getMessage());
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
        FileReader reader = new FileReader(
                "C:\\Users\\kylek\\repos\\PaperStreet\\src\\main\\java\\com\\paperstreet\\strategy\\strategy_parameters.json");
        return reader;
    }
}
