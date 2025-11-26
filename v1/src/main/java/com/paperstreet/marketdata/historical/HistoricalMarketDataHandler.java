package com.paperstreet.marketdata.historical;

import com.ib.client.*;
import com.paperstreet.marketdata.ContractHandler;
import com.paperstreet.marketdata.EWrapperImpl;
import com.paperstreet.utils.LogHandler;

import java.util.List;

import static com.paperstreet.marketdata.MarketDataConstants.BROKER_CONNECTION_IP;
import static com.paperstreet.marketdata.MarketDataConstants.BROKER_CONNECTION_PORT;
import static com.paperstreet.utils.ConnectionConstants.HISTORICAL_MARKET_DATA_CONNECTION_ID;

public class HistoricalMarketDataHandler {
    private final EClientSocket client;
    private final EReaderSignal signal;
    private EReader reader;
    private final LogHandler logHandler;

    public HistoricalMarketDataHandler() {
        logHandler = new LogHandler();
        this.signal = new EJavaSignal();
        EWrapperImpl wrapper = new EWrapperImpl();
        this.client = new EClientSocket(wrapper, signal);
    }

    public void connectMarketDataHandler() {
        client.eConnect(BROKER_CONNECTION_IP, BROKER_CONNECTION_PORT, HISTORICAL_MARKET_DATA_CONNECTION_ID);
        reader = new EReader(client, signal);
        reader.start();
        new Thread(() -> {
            if (client.isConnected()) {
                logHandler.logInfo("MarketDataHandler is now connected.");
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

    public void requestMarketData(String symbol) {

        // fine to leave tickId as static as long as there are no other methods requesting market data.
        // will need to make dynamic if I start trading multiple symbols I think.
        int tickId = 6;
        Contract contract = ContractHandler.getContract(symbol);
        String endDateTime = "20240519-23:59:59";
        String durationStr = "5 Y"; // day
        String barSizeSetting = "1 day";
        String whatToShow = "TRADES";
        int useRTH = 1; // use only RTH data (no data from outside of regular trading hours)
        int formatDate = 1; // obtain time as yyyyMMdd HH:mm:ss
        boolean keepUpToDate = false;
        List<TagValue> chartOptions = null; // no documentation on this so leaving as null

        client.reqHistoricalData(tickId, contract, endDateTime, durationStr, barSizeSetting,
                whatToShow, useRTH, formatDate, keepUpToDate, chartOptions);

    }
}
