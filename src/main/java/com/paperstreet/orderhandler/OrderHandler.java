package com.paperstreet.orderhandler;

import com.ib.client.*;
import com.paperstreet.marketdata.ContractHandler;
import com.paperstreet.marketdata.EWrapperImpl;
import com.paperstreet.utils.LogHandler;

import static com.paperstreet.marketdata.MarketDataConstants.BROKER_CONNECTION_IP;
import static com.paperstreet.marketdata.MarketDataConstants.BROKER_CONNECTION_PORT;
import static com.paperstreet.utils.ConnectionConstants.ORDER_HANDLER_CONNECTION_ID;

/**
 * Main module of the Order Management System. It connects to IBKR, receives the next valid order ID,
 * and is called by the strategy to submit orders.
 */
public class OrderHandler {

    private static int nextValidOrderId;
    private final EClientSocket clientSocket;
    private final EReaderSignal signal;
    private EReader reader;
    private final LogHandler logHandler;

    public OrderHandler() {
        this.signal = new EJavaSignal();
        EWrapperImpl wrapper = new EWrapperImpl();
        this.clientSocket = new EClientSocket(wrapper, signal);
        logHandler = new LogHandler();
    }

    /**
     * First establishes an API connection by requesting from the operating system that a TCP socket
     * be opened to the specified IP address and socket port. Then use the EReader class to read from
     * the socket and add messages to a queue. Everytime a new message is added to the message queue,
     * a notification flag is triggered to let other threads now that there is a message waiting to
     * be processed.
     */
    public void connectOrderHandler() {
        clientSocket.eConnect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, ORDER_HANDLER_CONNECTION_ID);
        reader = new EReader(clientSocket, signal);
        reader.start();
        new Thread(() -> {
            while (clientSocket.isConnected()) {
                signal.waitForSignal();
                try {
                    reader.processMsgs();
                } catch (Exception e) {
                    logHandler.logError("Exception: " + e.getMessage());
                }
            }
        }).start();
    }

    public void sendLimitOrder(String symbol, String side, double quantity, double price) {
        Contract contract = ContractHandler.getContract(symbol);
        int orderId = getValidOrderId();
        clientSocket.placeOrder(orderId, contract, OrderTypes.LimitOrder(side, quantity, price));
    }

    public void sendMarketOrder(String symbol, String side, double quantity) {
        Contract contract = ContractHandler.getContract(symbol);
        int orderId = getValidOrderId();
        clientSocket.placeOrder(orderId, contract, OrderTypes.MarketOrder(side, quantity));
    }

    public static void setNextValidId(int id) {
        OrderHandler.nextValidOrderId = id;
    }

    public int getValidOrderId() {
        return nextValidOrderId;
    }

    // for stop-loss and other secondary orders
    public static int getAdditionalValidOrderId() {
        nextValidOrderId+=2  ;
        return nextValidOrderId;
    }
}
