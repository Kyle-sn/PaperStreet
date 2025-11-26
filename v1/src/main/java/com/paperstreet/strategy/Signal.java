package com.paperstreet.strategy;

public class Signal {
    private final int strategy;
    private final String symbol;
    private final int quantity;

    public Signal(int strategy, String symbol, int quantity) {
        this.strategy = strategy;
        this.symbol = symbol;
        this.quantity = quantity;
    }

    @Override
    public String toString() {
        return strategy + "," + symbol + "," + quantity;
    }

    public int getStrategy() {
        return strategy;
    }

    public String getSymbol() {
        return symbol;
    }

    public int getQuantity() {
        return quantity;
    }
}
