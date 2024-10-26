package com.paperstreet.marketdata;

/**
 * Class with main method used to connect the MarketDataHandler.
 */
public class ConnectMarketDataHandler {

    private static final MarketDataHandler marketDataHandler = new MarketDataHandler();

    /**
     * Connect the MarketDataHandler and request market data for the relevant contract.
     * @param args
     */
    public static void main(String[] args) {
        marketDataHandler.connectMarketDataHandler();
        marketDataHandler.requestMarketData(MarketDataConstants.SYMBOL);
    }
}