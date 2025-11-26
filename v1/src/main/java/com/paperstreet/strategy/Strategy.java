package com.paperstreet.strategy;

import com.paperstreet.trades.Trade;

import java.util.ArrayList;
import java.util.List;

public class Strategy {
    private String name;
    private List<Trade> trades;

    public Strategy(String name) {
        this.name = name;
        this.trades = new ArrayList<>();
    }

    public String getName() {
        return name;
    }

    public List<Trade> getTrades() {
        return trades;
    }

    public void addTrade(Trade trade) {
        trades.add(trade);
    }
}
