package marketdata;

import static marketdata.MarketDataConstants.SYMBOL;

public class Connect {

    private static final MarketDataHandler marketDataHandler = new MarketDataHandler();

    public static void main(String[] args) {
        marketDataHandler.connectMarketDataHandler();
        marketDataHandler.requestMarketData(SYMBOL);
    }
}