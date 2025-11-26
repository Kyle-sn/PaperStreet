package com.paperstreet.positionhandler;

import com.ib.client.EClientSocket;
import com.ib.client.EJavaSignal;
import com.ib.client.EReader;
import com.ib.client.EReaderSignal;
import com.paperstreet.marketdata.EWrapperImpl;
import com.paperstreet.utils.LogHandler;

import static com.paperstreet.marketdata.MarketDataConstants.BROKER_CONNECTION_IP;
import static com.paperstreet.marketdata.MarketDataConstants.BROKER_CONNECTION_PORT;
import static com.paperstreet.utils.ConnectionConstants.POSITION_HANDLER_CONNECTION_ID;

/**
 * Class to initiate position handling.
 */
public class PositionHandler {

    private final EClientSocket client;
    private final EReaderSignal signal;
    private EReader reader;
    private final LogHandler logHandler;

    public PositionHandler() {
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
    public void connectPositionHandler() {
        client.eConnect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, POSITION_HANDLER_CONNECTION_ID);
        reader = new EReader(client, signal);
        reader.start();
        new Thread(() -> {
            if (client.isConnected()) {
                logHandler.logInfo("PositionHandler is now connected.");
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

    /**
     * Subscribes to a specific account's information and portfolio.
     *
     * @param bool set to true to start the subscription and to false stop it.
     * @param accountNumber the account id for which the information is requested.
     */
    public void requestAccountUpdates(boolean bool, String accountNumber) {
        client.reqAccountUpdates(bool, accountNumber);
    }

    /**
     * Requests a specific account's summary. In addition to the params below, a string of desired tags
     * to return information for is hardcoded.
     *
     * @param reqId the unique request identifier.
     * @param group set to "All" to return account summary data for all accounts.
     */
    public void requestAccountSummary(int reqId, String group) {
        client.reqAccountSummary(reqId, group, "AccountType,NetLiquidation,TotalCashValue,SettledCash," +
                "AccruedCash,BuyingPower,EquityWithLoanValue,PreviousEquityWithLoanValue,GrossPositionValue," +
                "ReqTEquity,ReqTMargin,SMA,InitMarginReq,MaintMarginReq,AvailableFunds,ExcessLiquidity,Cushion," +
                "FullInitMarginReq,FullMaintMarginReq,FullAvailableFunds,FullExcessLiquidity,LookAheadNextChange," +
                "LookAheadInitMarginReq ,LookAheadMaintMarginReq,LookAheadAvailableFunds,LookAheadExcessLiquidity," +
                "HighestSeverity,DayTradesRemaining,Leverage");
    }

    /**
     * Subscribes to position updates for all accessible accounts. All positions sent initially,
     * and then only updates as positions change.
     */
    public void requestPositions() {
        client.reqPositions();
    }
}