package com.paperstreet.strategy;

import com.ib.client.*;
import com.paperstreet.marketdata.ContractHandler;
import com.paperstreet.marketdata.EWrapperImpl;
import com.paperstreet.trades.OrderTypes;
import com.paperstreet.utils.LogHandler;

import java.io.FileNotFoundException;
import java.util.List;
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

    public void placeTrade() throws InterruptedException, FileNotFoundException {
        TimeUnit.SECONDS.sleep(2);
        List<Integer> strategyIds = StrategyParameterReader.getStrategyIds();

        // loop through all strategies in the strategy_parameter.json file and place trades
        // according to the strategy parameters and strategy signals.
        for (int strategyId : strategyIds) {
            String symbol = getSymbol(strategyId);
            int quantity = getSignalQuantity(strategyId);

            if (quantity == 0) {
                logHandler.logInfo("Strategy " + strategyId + " does not have a trade signal today. Taking no action.");
            } else {
                String signalSide = quantity > 0 ? "BUY" : "SELL";
                if (signalSide.equals("SELL")) {
                    quantity = quantity * -1;
                }
                if (PreTradeChecks.passedPreTradeChecks(strategyId, signalSide, quantity)) {
                    TimeUnit.SECONDS.sleep(2);
                    sendMarketOrder(symbol, signalSide, quantity);
                } else {
                    logHandler.logError("Pre-trade checks failed. Strategy " + strategyId + " tried to " +
                            signalSide + " " + quantity + " of " + symbol + ". Check the current position size " +
                            "and if the strategy is allowed to short.");
                }
            }
        }
    }

    public void sendMarketOrder(String symbol, String side, int quantity) {
        Contract contract = ContractHandler.getContract(symbol);
        int orderId = getValidOrderId();
        client.placeOrder(orderId, contract, OrderTypes.marketOrder(side, quantity));
        nextValidOrderId++;
    }

    public static String getSymbol(int strategyId) {
        Object symbolObj = StrategyParameterReader.getParam("symbol", strategyId);
        assert symbolObj != null;
        return (String) symbolObj;
    }

    public static void setNextValidId(int id) {
        nextValidOrderId = id;
    }

    public static int getValidOrderId() {
        return nextValidOrderId;
    }

    private static int getSignalQuantity(int strategyId) throws FileNotFoundException {
        String tradeSignal = SignalReader.getSpecificStrategySignal(strategyId);
        if (tradeSignal == null || tradeSignal.isEmpty()) {
            return 0;
        }

        String[] signalParams = tradeSignal.split(",");
        // check that there are only three parts of the signal
        if (signalParams.length < 3) {
            return 0;
        }
        return Integer.parseInt(signalParams[2]);
    }
}
