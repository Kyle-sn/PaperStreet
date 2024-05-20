package com.paperstreet.marketdata.historical;

import com.paperstreet.marketdata.MarketDataConstants;

public class ConnectHistoricalMarketDataHandler {

    private static final HistoricalMarketDataHandler historicalMarketDataHandler = new HistoricalMarketDataHandler();

    public static void main(String[] args) {
        historicalMarketDataHandler.connectMarketDataHandler();
        historicalMarketDataHandler.requestMarketData(MarketDataConstants.SYMBOL);
    }
}
