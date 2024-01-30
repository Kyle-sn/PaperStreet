package com.paperstreet.positionhandler;

import com.ib.client.Decimal;

import java.util.HashMap;
import java.util.Map;

public class PositionManager {

    private Map<String, Position> positionInfo;

    public PositionManager() {
        positionInfo = new HashMap<>();
    }

    public void getPosition(String symbol, Decimal quantity, double marketPrice, double marketValue,
                            double averageCost, double unrealizedPnl, double realizedPnl, String accountName) {

        Position newPosition = new Position();
        newPosition.setSymbol(symbol);
        newPosition.setQuantity(quantity);
        newPosition.setMarketPrice(marketPrice);
        newPosition.setMarketValue(marketValue);
        newPosition.setAverageCost(averageCost);
        newPosition.setUnrealizedPnl(unrealizedPnl);
        newPosition.setRealizedPnl(realizedPnl);

        positionInfo.put(accountName, newPosition);
    }

}
