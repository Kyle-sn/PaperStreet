package com.paperstreet.strategy;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

public class SignalReader {

    public static List<Signal> getSignals(int strategyId) throws FileNotFoundException {
        File file = new File("C:\\Users\\kylek\\data\\signals\\test_signal.csv");
        Scanner scanner = new Scanner(file);
        List<Signal> signals = new ArrayList<>();

        // skip the header line
        if (scanner.hasNextLine()) {
            scanner.nextLine();
        }

        while (scanner.hasNextLine()) {
            String line = scanner.nextLine();
            String[] parts = line.split(",");
            int strategy = Integer.parseInt(parts[0]);
            String symbol = parts[1];
            int quantity = Integer.parseInt(parts[2]);

            signals.add(new Signal(strategy, symbol, quantity));
        }
        scanner.close();
        return signals;
    }

    public static String getSpecificStrategySignal(int strategyId) throws FileNotFoundException {
        List<Signal> signals = getSignals(strategyId);
        for (Signal signal : signals) {
            if (signal.getStrategy() == strategyId) {
                return signal.toString();
            }
        }
        return ""; //return nothing
    }
}