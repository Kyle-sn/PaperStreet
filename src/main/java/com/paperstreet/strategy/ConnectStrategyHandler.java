package com.paperstreet.strategy;

/**
 * Class with main method used to connect the StrategyHandler.
 */
public class ConnectStrategyHandler {

    private static final StrategyHandler strategyHandler = new StrategyHandler();

    /**
     * Connects the StrategyHandler and then places a trade based on the underlying strategy logic.
     * @param args
     * @throws InterruptedException
     */
    public static void main(String[] args) throws InterruptedException {
        strategyHandler.connectStrategyHandler();
        strategyHandler.placeTrade();
    }
}
