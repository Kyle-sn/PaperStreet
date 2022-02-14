package marketdata;

/**
 * Market data constants.
 */
public class MarketDataConstants {

    /** Type of market data currently requested by broker - 1 real-time market data; 3 delayed market data */
    public static final int MARKET_DATA_TYPE = 3;

    public static final String BROKER_CONNECTION_IP = "127.0.0.1";

    public static final int BROKER_CONNECTION_PORT = 7496;

    /** Broker API tick type String indicating which tick values to receive from market data */
    public static final String TICK_STRING = "221";

    /** Symbol to request market data for */
    public static final String SYMBOL = "NQ";

    /** Stock security type */
    public static final String SECURITY_TYPE = "FUT"; // STK

    /** Stock exchange routing */
    public static final String EXCHANGE = "GLOBEX"; // SMART

    /** Stock currency */
    public static final String CURRENCY = "USD";

}