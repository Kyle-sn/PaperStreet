package com.paperstreet.marketdata;

/**
 * Market data constants.
 */
public class MarketDataConstants {

    /** Type of market data currently requested by broker - 1 real-time market data; 3 delayed market data */
    public static final int MARKET_DATA_TYPE = 3;

    /**
     * IP to connect to.
     */
    public static final String BROKER_CONNECTION_IP = "127.0.0.1";

    /**
     * Port to connect to. 7496 = prod | 7497 = paper account.
     */
    public static final int BROKER_CONNECTION_PORT = 7497;

    /** Broker API tick type String indicating which tick values to receive from market data */
    public static final String TICK_STRING = "221";

    /** Symbol to request market data for */
    public static final String SYMBOL = "QQQ";

    /** Stock security type */
    public static final String SECURITY_TYPE = "STK"; // FUT

    /** Stock exchange routing */
    public static final String EXCHANGE = "SMART"; // GLOBEX

    /** Stock currency */
    public static final String CURRENCY = "USD";

}