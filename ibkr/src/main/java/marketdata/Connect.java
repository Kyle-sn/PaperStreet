// look at https://github.com/bryanvandraanen/Penny/tree/234b9bb6e49c576dfdc7b6eea43215b211585e5b/src/main/java/penny
// for ideas

package marketdata;

import static marketdata.MarketDataConstants.SYMBOL;

public class Connect {
    private static final MarketDataHandler marketDataHandler = new MarketDataHandler();

    public static void main(String[] args) {
        marketDataHandler.connect();
        marketDataHandler.requestMarketData(SYMBOL);
    }

}