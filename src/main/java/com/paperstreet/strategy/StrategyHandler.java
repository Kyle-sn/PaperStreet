package com.paperstreet.strategy;

import com.ib.client.*;
import com.opencsv.exceptions.CsvValidationException;
import com.paperstreet.marketdata.ContractHandler;
import com.paperstreet.marketdata.EWrapperImpl;
import com.paperstreet.utils.LogHandler;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

import static com.paperstreet.marketdata.MarketDataConstants.BROKER_CONNECTION_IP;
import static com.paperstreet.marketdata.MarketDataConstants.BROKER_CONNECTION_PORT;
import static com.paperstreet.utils.ConnectionConstants.STRATEGY_HANDLER_CONNECTION_ID;

//TODO: create tests that cover the following
// quantity != 0
// correctly negating quantity if signal == SELL
// checkValidTradeSize
// quantityAfterTrade < 0 && !canShort

public class StrategyHandler {

    static int nextValidOrderId;
    static int posSize;
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
        TimeUnit.SECONDS.sleep(2);

        try {
            posSize = StrategyUtils.readPositionData();
        } catch (CsvValidationException | IOException e) {
            throw new RuntimeException(e);
        }

        logHandler.logInfo("Current position size is " + posSize);
        //TODO: read in signal size and side so it isnt hardcoded below
        String signalSide = "SELL";
        int quantity = 500;
        if (signalSide == "SELL") {
            quantity = quantity * -1;
        }

        Object symbolObj = StrategyParameterReader.getParam("symbol");
        assert symbolObj != null;
        String symbol = symbolObj.toString();

        Object maxPosObj = StrategyParameterReader.getParam("max_pos");
        assert maxPosObj != null;
        int maxPos = (Integer) maxPosObj;

        boolean validTradeSize = checkValidTradeSize(quantity, maxPos);
        if (!validTradeSize) {
            logHandler.logError("Error placing trade. Trade quantity of " + quantity +
                    " is greater than the configured max position limit of " + maxPos);
            return;
        }

        Object canShortObj = StrategyParameterReader.getParam("can_short");
        assert canShortObj != null;
        boolean canShort = (boolean) canShortObj;

        // According to IBKR "For general account types, a SELL order will be able to enter a short position
        // automatically if the order quantity is larger than your current long position."
        //TODO: create a method to do the below check. Will need for future tests.
        int quantityAfterTrade = quantity - posSize;
        if (quantityAfterTrade < 0 && !canShort) {
            logHandler.logError("Error placing trade. If trade is placed, the position will be negative and " +
                    "this strategy is not configured to trade short.");
            return;
        }
        sendMarketOrder(symbol, signalSide, quantity);
    }

    public void sendMarketOrder(String symbol, String side, int quantity) {
        Contract contract = ContractHandler.getContract(symbol);
        int orderId = getValidOrderId();
        client.placeOrder(orderId, contract, OrderTypes.MarketOrder(side, quantity));
    }

    private static boolean checkValidTradeSize(int quantity, int maxPos) {
        return quantity <= maxPos;
    }

    public static void setNextValidId(int id) {
        nextValidOrderId = id;
    }

    public static int getValidOrderId() {
        return nextValidOrderId;
    }
}
