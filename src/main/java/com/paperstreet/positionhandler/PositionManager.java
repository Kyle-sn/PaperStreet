package com.paperstreet.positionhandler;

import com.ib.client.Decimal;

import java.io.FileWriter;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * Collect position information to be monitored.
 */
public class PositionManager {

    private static Map<String, Positions> positionsMap;

    public PositionManager() {
        positionsMap = new HashMap<>();
    }

    public void getPositions(String symbol, Decimal quantity, double averageCost, String accountName) {

        Positions positions = new Positions();
        positions.setSymbol(symbol);
        positions.setQuantity(quantity);
        positions.setAverageCost(averageCost);
        positions.setAccountNumber(accountName);

        positionsMap.put(symbol, positions);
    }

    public void savePositionsToCsv(String filePath) {
        try (FileWriter writer = new FileWriter(filePath)) {
            writer.append("symbol,quantity,averageCost,accountNumber\n");
            for (Map.Entry<String, Positions> entry : positionsMap.entrySet()) {
                Positions positions = entry.getValue();
                writer.append(positions.getSymbol()).append(",");
                writer.append(positions.getQuantity().toString()).append(",");
                writer.append(Double.toString(positions.getAverageCost())).append(",");
                writer.append(positions.getAccountNumber()).append("\n");
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
