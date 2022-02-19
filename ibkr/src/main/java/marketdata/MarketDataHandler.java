package marketdata;

import com.ib.client.*;

import static marketdata.MarketDataConstants.*;

/**
 * Main module of the Market Data Capture. It connects to IBKR, returns callback information
 * related to market data, and specifies what type of market data we are requesting.
 */
public class MarketDataHandler {

    private final EClientSocket client;
    private final EReaderSignal signal;
    private EReader reader;

    public MarketDataHandler() {
        this.signal = new EJavaSignal();
        EWrapperImpl wrapper = new EWrapperImpl();
        this.client = new EClientSocket(wrapper, signal);
    }

    /**
     * First establishes an API connection by requesting from the operating system that a TCP socket
     * be opened to the specified IP address and socket port. Then use the EReader class to read from
     * the socket and add messages to a queue. Everytime a new message is added to the message queue,
     * a notification flag is triggered to let other threads now that there is a message waiting to
     * be processed.
     */
    public void connectMarketDataHandler() {
        client.eConnect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, 2 /* clientID */);
        reader = new EReader(client, signal);
        reader.start();
        new Thread(() -> {
            while (client.isConnected()) {
                signal.waitForSignal();
                try {
                    reader.processMsgs();
                } catch (Exception e) {
                    System.out.println("Exception: " + e.getMessage());
                }
            }
        }).start();
    }

    /**
     * Requests market data for the specified symbol. This data is not tick-by-tick but consists
     * of aggregated snapshots taken at intra-second intervals which differ depending on the type
     * of instrument.
     *
     * @param symbol The stock ticker to request market data for
     */
    public void requestMarketData(String symbol) {
        Contract contract = ContractHandler.getContract(symbol);
        int tickId = 5;

        client.reqMarketDataType(MARKET_DATA_TYPE);
        client.reqMktData(tickId, contract, TICK_STRING,
                false /* Snapshot */, false /* Regulatory Snapshot */, null /* MktDataOptions */);
    }
}