package com.paperstreet.positionhandler;

import com.ib.client.Decimal;

import java.util.HashMap;
import java.util.Map;

/**
 * Collect position information to be monitored.
 */
public class PositionManager {

    private Map<String, Positions> positionsMap;

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
}
