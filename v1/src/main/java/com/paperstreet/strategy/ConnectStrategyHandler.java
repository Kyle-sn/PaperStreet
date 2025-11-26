package com.paperstreet.strategy;

import java.io.FileNotFoundException;

public class ConnectStrategyHandler {

    private static final StrategyHandler strategyHandler = new StrategyHandler();

    public static void main(String[] args) throws InterruptedException, FileNotFoundException {
        strategyHandler.connectStrategyHandler();
        strategyHandler.placeTrade();
    }
}
