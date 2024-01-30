package com.paperstreet.strategy;

public class ConnectStrategyHandler {

    private static final StrategyHandler strategyHandler = new StrategyHandler();

    public static void main(String[] args) throws InterruptedException {
        strategyHandler.connectStrategyHandler();
        strategyHandler.placeTrade();
    }
}
