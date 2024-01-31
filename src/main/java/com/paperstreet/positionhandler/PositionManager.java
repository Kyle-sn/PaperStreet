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

    public void getPositions(String symbol, Decimal quantity, double marketPrice,
                             double marketValue, double averageCost, double unrealizedPnl,
                             double realizedPnl, String accountName) {

        Positions positions = new Positions();
        positions.setSymbol(symbol);
        positions.setQuantity(quantity);
        positions.setMarketPrice(marketPrice);
        positions.setMarketValue(marketValue);
        positions.setAverageCost(averageCost);
        positions.setUnrealizedPnl(unrealizedPnl);
        positions.setRealizedPnl(realizedPnl);
        positions.setAccountNumber(accountName);

        positionsMap.put(symbol, positions);
    }
}
