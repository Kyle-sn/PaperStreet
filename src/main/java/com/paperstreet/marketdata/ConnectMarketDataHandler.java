package com.paperstreet.marketdata;

public class ConnectMarketDataHandler {

    private static final MarketDataHandler marketDataHandler = new MarketDataHandler();

    public static void main(String[] args) {
        marketDataHandler.connectMarketDataHandler();
        marketDataHandler.requestMarketData(MarketDataConstants.SYMBOL);
    }
}