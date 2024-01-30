package com.paperstreet.strategy;

import com.ib.client.*;
import com.paperstreet.marketdata.ContractHandler;
import com.paperstreet.marketdata.EWrapperImpl;
import com.paperstreet.marketdata.MarketDataConstants;
import com.paperstreet.utils.LogHandler;

import java.util.concurrent.TimeUnit;

import static com.paperstreet.marketdata.MarketDataConstants.BROKER_CONNECTION_IP;
import static com.paperstreet.marketdata.MarketDataConstants.BROKER_CONNECTION_PORT;
import static com.paperstreet.utils.ConnectionConstants.STRATEGY_HANDLER_CONNECTION_ID;

public class StrategyHandler {

     static int nextValidOrderId;
    private final EReaderSignal signal;
    private final EClientSocket client;
    private EReader reader;
    private final LogHandler logHandler;

    public StrategyHandler() {
        this.signal = new EJavaSignal();
        EWrapperImpl wrapper = new EWrapperImpl();
        this.client = new EClientSocket(wrapper, signal);
        logHandler = new LogHandler();
    }

    /**
     * First establishes an API connection by requesting from the operating system that a TCP socket
     * be opened to the specified IP address and socket port. Then use the EReader class to read from
     * the socket and add messages to a queue. Everytime a new message is added to the message queue,
     * a notification flag is triggered to let other threads now that there is a message waiting to
     * be processed.
     */
    public void connectStrategyHandler() {
        client.eConnect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, STRATEGY_HANDLER_CONNECTION_ID);
        reader = new EReader(client, signal);
        reader.start();
        new Thread(() -> {
            if (client.isConnected()) {
                logHandler.logInfo("StrategyHandler is now connected.");
            }

            while (client.isConnected()) {
                signal.waitForSignal();
                try {
                    reader.processMsgs();
                } catch (Exception e) {
                    logHandler.logError("Exception: " + e.getMessage());
                }
            }
        }).start();
    }

    public void placeTrade() throws InterruptedException {
        TimeUnit.SECONDS.sleep(5);
        sendMarketOrder(MarketDataConstants.SYMBOL, "BUY", 1000);
    }

    public void sendMarketOrder(String symbol, String side, double quantity) {
        Contract contract = ContractHandler.getContract(symbol);
        int orderId = getValidOrderId();
        client.placeOrder(orderId, contract, OrderTypes.MarketOrder(side, quantity));
    }

    public static void setNextValidId(int id) {
        nextValidOrderId = id;
    }

    public static int getValidOrderId() {
        return nextValidOrderId;
    }
}
