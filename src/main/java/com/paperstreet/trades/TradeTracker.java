package com.paperstreet.trades;

import com.paperstreet.strategy.Strategy;

import java.util.HashMap;
import java.util.Map;

public class TradeTracker {
    private final Map<String, Strategy> strategies;

    public TradeTracker() {
        this.strategies = new HashMap<>();
    }

    public void addStrategy(Strategy strategy) {
        strategies.put(strategy.getName(), strategy);
    }

    public void addTrade(String strategyName, Trade trade) {
        Strategy strategy = strategies.get(strategyName);
        if (strategy != null) {
            strategy.addTrade(trade);
        } else {
            System.out.println("Strategy not found: " + strategyName);
        }
    }

    public Strategy getStrategy(String strategyName) {
        return strategies.get(strategyName);
    }

    public Map<String, Strategy> getStrategies() {
        return strategies;
    }

    // TODO: make a test out of the below main function
    // TODO: apply this logic in a dynamic way within the StrategyHandler
    public static void main(String[] args) {
        TradeTracker tracker = new TradeTracker();

        // creating strategies
        Strategy strategy1 = new Strategy("Strategy1");
        Strategy strategy2 = new Strategy("Strategy2");

        // adding strategies to tracker
        tracker.addStrategy(strategy1);
        tracker.addStrategy(strategy2);

        // creating trades
        Trade trade1 = new Trade(123, 1, "BUY", 20);
        Trade trade2 = new Trade(234, 2, "SELL", 21);

        // adding trades to strategies
        tracker.addTrade("Strategy1", trade1);
        tracker.addTrade("Strategy2", trade2);

        // retrieving and displaying strategy trades
        System.out.println(tracker.getStrategy("Strategy1"));
        System.out.println(tracker.getStrategy("Strategy2"));
    }
}

