package linehandler;

import com.ib.client.*;
import marketdata.ContractHandler;
import marketdata.EWrapperImpl;

import java.time.LocalDateTime;

import static marketdata.MarketDataConstants.BROKER_CONNECTION_IP;
import static marketdata.MarketDataConstants.BROKER_CONNECTION_PORT;

// TODO: add javadoc explaining this module
public class OrderHandler {

    private static EClient client;
    private static int nextValidOrderId;
    private final EClientSocket clientSocket;
    private final EReaderSignal signal;
    private EReader reader;

    public OrderHandler() {
        this.signal = new EJavaSignal();
        EWrapperImpl wrapper = new EWrapperImpl();
        this.clientSocket = new EClientSocket(wrapper, signal);
    }

    /**
     * First establishes an API connection by requesting from the operating system that a TCP socket
     * be opened to the specified IP address and socket port. Then use the EReader class to read from
     * the socket and add messages to a queue. Everytime a new message is added to the message queue,
     * a notification flag is triggered to let other threads now that there is a message waiting to
     * be processed.
     */
    public void connectOrderHandler() {
        //TODO: make the clientId dynamic
        //TODO: make sure it is not the same as the MarketDataHandlers connection (a simple check  should suffice)
        clientSocket.eConnect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, 3 /* clientID */);
        reader = new EReader(clientSocket, signal);
        reader.start();
        new Thread(() -> {
            while (clientSocket.isConnected()) {
                signal.waitForSignal();
                try {
                    reader.processMsgs();
                } catch (Exception e) {
                    System.out.println("Exception: " + e.getMessage());
                }
            }
        }).start();
    }

    public void sendLimitOrder(String symbol, String side, double quantity, double price) {
        Contract contract = ContractHandler.getContract(symbol);
        int orderId = getValidOrderId();
        // TODO: fx NullPointerExeption I keep getting. Currently not sending orders correctly.
        try {
            client.placeOrder(orderId,
                    contract,
                    OrderTypes.LimitOrder(side, quantity, price));
        } catch (NullPointerException e) {
            System.out.println(e);
        }

        LocalDateTime timeStamp = LocalDateTime.now();

        System.out.println(timeStamp + ": order=limit_order,side=" + side + ",quantity=" +
                quantity + ",symbol=" + symbol + ",price=" + price);
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
