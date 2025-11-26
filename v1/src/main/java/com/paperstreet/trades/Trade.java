package com.paperstreet.trades;

public class Trade {
    private int strategyId;
    private int tradeId;
    private int quantity;
    private String side;

    public Trade(int strategyId, int quantity, String side, int tradeId) {
        this.strategyId = strategyId;
        this.quantity = quantity;
        this.side = side;
        this.tradeId = tradeId;
    }

    public int getStrategyId() {
        return strategyId;
    }

    public int getTradeId() {
        return tradeId;
    }

    public int getQuantity() {
        return quantity;
    }

    public String getSide() {
        return side;
    }
}
