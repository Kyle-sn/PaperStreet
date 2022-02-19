package marketdata;

import com.ib.client.*;
import linehandler.OrderHandler;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;

import static marketdata.MarketDataConstants.SYMBOL;

/**
 * This interface's methods are used by the TWS/Gateway to communicate with the API client. Every API client
 * application needs to implement this interface in order to handle all the events generated by the TWS/Gateway.
 * Almost every EClientSocket method call will result in at least one event delivered here.
 */
public class EWrapperImpl implements EWrapper {

    private final EReaderSignal readerSignal;
    private final EClientSocket clientSocket;
    private final MarketDataWriter writer;

    public EWrapperImpl() {
        readerSignal = new EJavaSignal();
        clientSocket = new EClientSocket(this, readerSignal);
        writer = new MarketDataWriter();
    }

    /**
     * Market data tick price callback. Handles all price related ticks. Every tickPrice callback
     * is followed by a tickSize. A tickPrice value of -1 or 0 followed by a tickSize of 0 indicates
     * there is no data for this field currently available, whereas a tickPrice with a positive tickSize
     * indicates an active quote of 0 (typically for a combo contract).
     *
     * @param tickerId the request's unique identifier.
     * @param field the type of the price being received (i.e. ask price).
     * @param price the actual price.
     * @param attribs an TickAttrib object that contains price attributes
     */
    @Override
    public void tickPrice(int tickerId, int field, double price, TickAttrib attribs) {
        LocalDateTime timeStamp = LocalDateTime.now();
        try {
            writer.writeTicks(timeStamp,SYMBOL, TickType.getField(field), price);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void tickSize(int tickerId, int field, Decimal size) {
    }

    @Override
    public void tickOptionComputation(int tickerId, int field, int tickAttrib, double impliedVol, double delta, double optPrice,
                                      double pvDividend, double gamma, double vega, double theta, double undPrice) {

    }

    @Override
    public void tickGeneric(int tickerId, int tickType, double value) {

    }

    @Override
    public void tickString(int tickerId, int tickType, String value) {

    }

    @Override
    public void tickEFP(int tickerId, int tickType, double basisPoints,
                        String formattedBasisPoints, double impliedFuture, int holdDays,
                        String futureLastTradeDate, double dividendImpact,
                        double dividendsToLastTradeDate) {

    }

    /**
     * Gives the up-to-date information of an order every time it changes. Often there are duplicate orderStatus messages.
     *
     * @param orderId the order's client id.
     * @param status the current status of the order.
     * @param filled number of filled positions.
     * @param remaining the remnant positions.
     * @param avgFillPrice average filling price.
     * @param permId the order's permId used by the TWS to identify orders.
     * @param parentId parent's id. Used for bracket and auto trailing stop orders.
     * @param lastFillPrice price at which the last positions were filled.
     * @param clientId API client which submitted the order.
     * @param whyHeld this field is used to identify an order held when TWS is trying to locate shares
     *               for a short sell. The value used to indicate this is 'locate'.
     * @param mktCapPrice If an order has been capped, this indicates the current capped price.
     */
    @Override
    public void orderStatus(int orderId, String status, Decimal filled, Decimal remaining, double avgFillPrice,
                            int permId, int parentId, double lastFillPrice, int clientId, String whyHeld, double mktCapPrice) {
        System.out.println("ORDER_STATUS_CALLBACK: orderId: " + orderId + ", status: " + status + ", filled: " + filled +
                ", remaining: " + remaining + ", avgFillPrice: " + avgFillPrice + ", permId: " + permId +
                ", parentId: " + parentId + ", lastFillPrice: " + lastFillPrice + ", clientId: " + clientId +
                ", whyHeld: " + whyHeld + ", mktCapPrice: " + mktCapPrice);
    }

    /**
     * Feeds in currently open orders.
     *
     * @param orderId the order's unique id
     * @param contract the order's Contract.
     * @param order the currently active Order.
     * @param orderState the order's OrderState
     */
    @Override
    public void openOrder(int orderId, Contract contract, Order order,
                          OrderState orderState) {
        System.out.println("OPEN_ORDER_CALLBACK: orderId: " + orderId + ", contract: " + contract.symbol() +
                ", order: " + order + ", orderState: " + orderState);
    }

    @Override
    public void openOrderEnd() {

    }

    @Override
    public void updateAccountValue(String key, String value, String currency,
                                   String accountName) {

    }

    @Override
    public void updatePortfolio(Contract contract, Decimal position, double marketPrice, double marketValue,
                                double averageCost, double unrealizedPNL, double realizedPNL, String accountName) {

    }

    @Override
    public void updateAccountTime(String timeStamp) {

    }

    @Override
    public void accountDownloadEnd(String accountName) {

    }

    /**
     * The nextValidId event provides the next valid identifier needed to place an order. This identifier
     * is nothing more than the next number in the sequence. This means that if there is a single client
     * application submitting orders to an account, it does not have to obtain a new valid identifier every
     * time it needs to submit a new order. It is enough to increase the last value received from the
     * nextValidId method by one. For example, if the valid identifier for your first API order is 1, the
     * next valid identifier would be 2 and so on. The next valid identifier is persistent between TWS sessions.
     *
     * @param orderId callback of the next valid ID.
     */
    @Override
    public void nextValidId(int orderId) {
        System.out.println(EWrapperMsgGenerator.nextValidId(orderId));
        OrderHandler.setNextValidId(orderId);
    }

    @Override
    public void contractDetails(int reqId, ContractDetails contractDetails) {

    }

    @Override
    public void bondContractDetails(int reqId, ContractDetails contractDetails) {

    }

    @Override
    public void contractDetailsEnd(int reqId) {

    }

    @Override
    public void execDetails(int reqId, Contract contract, Execution execution) {

    }

    @Override
    public void execDetailsEnd(int reqId) {

    }

    @Override
    public void updateMktDepth(int tickerId, int position, int operation, int side, double price, Decimal size) {

    }

    @Override
    public void updateMktDepthL2(int tickerId, int position, String marketMaker, int operation, int side, double price,
                                 Decimal size, boolean isSmartDepth) {

    }

    @Override
    public void updateNewsBulletin(int msgId, int msgType, String message,
                                   String origExchange) {

    }

    @Override
    public void managedAccounts(String accountsList) {

    }

    @Override
    public void receiveFA(int faDataType, String xml) {

    }

    @Override
    public void historicalData(int reqId, Bar bar) {

    }

    @Override
    public void historicalDataEnd(int reqId, String startDateStr, String endDateStr) {

    }

    @Override
    public void scannerParameters(String xml) {

    }

    @Override
    public void scannerData(int reqId, int rank,
                            ContractDetails contractDetails, String distance, String benchmark,
                            String projection, String legsStr) {

    }

    @Override
    public void scannerDataEnd(int reqId) {

    }

    @Override
    public void realtimeBar(int reqId, long date, double open, double high, double low, double close,
                            Decimal volume, Decimal wap, int count) {

    }

    @Override
    public void currentTime(long time) {
    }

    @Override
    public void fundamentalData(int reqId, String data) {

    }

    @Override
    public void deltaNeutralValidation(int reqId, DeltaNeutralContract deltaNeutralContract) {

    }

    @Override
    public void tickSnapshotEnd(int reqId) {

    }

    @Override
    public void marketDataType(int reqId, int marketDataType) {
        System.out.println("Market data type: ["+marketDataType+"]\n");
    }

    @Override
    public void commissionReport(CommissionReport commissionReport) {

    }

    @Override
    public void position(String account, Contract contract, Decimal pos, double avgCost) {

    }

    @Override
    public void positionEnd() {

    }

    @Override
    public void accountSummary(int reqId, String account, String tag,
                               String value, String currency) {

    }

    @Override
    public void accountSummaryEnd(int reqId) {

    }

    @Override
    public void verifyMessageAPI(String apiData) {

    }

    @Override
    public void verifyCompleted(boolean isSuccessful, String errorText) {

    }

    @Override
    public void verifyAndAuthMessageAPI(String apiData, String xyzChallenge) {

    }

    @Override
    public void verifyAndAuthCompleted(boolean isSuccessful, String errorText) {

    }

    @Override
    public void displayGroupList(int reqId, String groups) {

    }

    @Override
    public void displayGroupUpdated(int reqId, String contractInfo) {

    }

    @Override
    public void error(Exception e) {
        System.out.println("ERROR: Exception: "+e.getMessage());
    }

    @Override
    public void error(String str) {
        System.out.println("ERROR: " + str);
    }

    @Override
    public void error(int id, int errorCode, String errorMsg) {
        System.out.println("ERROR: Id: " + id + ", Code: " + errorCode + ", Msg: " + errorMsg);
    }

    @Override
    public void connectionClosed() {
        System.out.println("Connection closed");
    }

    @Override
    public void connectAck() {
        if (clientSocket.isAsyncEConnect()) {
            System.out.println("Acknowledging connection");
            clientSocket.startAPI();
        }
    }

    @Override
    public void positionMulti(int requestId, String account, String modelCode, Contract contract, Decimal pos,
                              double avgCost) {

    }

    @Override
    public void positionMultiEnd(int reqId) {

    }

    @Override
    public void accountUpdateMulti(int reqId, String account, String modelCode,
                                   String key, String value, String currency) {

    }

    @Override
    public void accountUpdateMultiEnd(int reqId) {

    }

    @Override
    public void securityDefinitionOptionalParameter(int reqId, String exchange,
                                                    int underlyingConId, String tradingClass, String multiplier,
                                                    Set<String> expirations, Set<Double> strikes) {

    }

    @Override
    public void securityDefinitionOptionalParameterEnd(int reqId) {

    }

    @Override
    public void softDollarTiers(int reqId, SoftDollarTier[] tiers) {

    }

    @Override
    public void familyCodes(FamilyCode[] familyCodes) {

    }

    @Override
    public void symbolSamples(int reqId, ContractDescription[] contractDescriptions) {

    }

    @Override
    public void mktDepthExchanges(DepthMktDataDescription[] depthMktDataDescriptions) {

    }

    @Override
    public void tickNews(int tickerId, long timeStamp, String providerCode,
                         String articleId, String headline, String extraData) {

    }

    @Override
    public void smartComponents(int reqId, Map<Integer, Entry<String, Character>> theMap) {

    }

    @Override
    public void tickReqParams(int tickerId, double minTick, String bboExchange, int snapshotPermissions) {

    }

    @Override
    public void newsProviders(NewsProvider[] newsProviders) {

    }

    @Override
    public void newsArticle(int requestId, int articleType, String articleText) {

    }

    @Override
    public void historicalNews(int requestId, String time, String providerCode, String articleId, String headline) {

    }

    @Override
    public void historicalNewsEnd(int requestId, boolean hasMore) {

    }

    @Override
    public void headTimestamp(int reqId, String headTimestamp) {

    }

    @Override
    public void histogramData(int reqId, List<HistogramEntry> items) {

    }

    @Override
    public void historicalDataUpdate(int reqId, Bar bar) {

    }

    @Override
    public void rerouteMktDataReq(int reqId, int conId, String exchange) {

    }

    @Override
    public void rerouteMktDepthReq(int reqId, int conId, String exchange) {

    }

    @Override
    public void marketRule(int marketRuleId, PriceIncrement[] priceIncrements) {

    }

    @Override
    public void pnl(int reqId, double dailyPnL, double unrealizedPnL, double realizedPnL) {

    }

    @Override
    public void pnlSingle(int reqId, Decimal pos, double dailyPnL, double unrealizedPnL, double realizedPnL, double value) {

    }

    @Override
    public void historicalTicks(int reqId, List<HistoricalTick> ticks, boolean done) {

    }

    @Override
    public void historicalTicksBidAsk(int reqId, List<HistoricalTickBidAsk> ticks, boolean done) {

    }

    @Override
    public void historicalTicksLast(int reqId, List<HistoricalTickLast> ticks, boolean done) {

    }

    @Override
    public void tickByTickAllLast(int reqId, int tickType, long time, double price, Decimal size,
                                  TickAttribLast tickAttribLast, String exchange, String specialConditions) {

    }

    @Override
    public void tickByTickBidAsk(int reqId, long time, double bidPrice, double askPrice, Decimal bidSize,
                                 Decimal askSize, TickAttribBidAsk tickAttribBidAsk) {

    }

    @Override
    public void tickByTickMidPoint(int reqId, long time, double midPoint) {

    }

    @Override
    public void orderBound(long orderId, int apiClientId, int apiOrderId) {

    }

    @Override
    public void completedOrder(Contract contract, Order order, OrderState orderState) {

    }

    @Override
    public void completedOrdersEnd() {

    }

    @Override
    public void replaceFAEnd(int reqId, String text) {

    }

    @Override
    public void wshMetaData(int reqId, String dataJson) {

    }

    @Override
    public void wshEventData(int reqId, String dataJson) {

    }

    @Override
    public void historicalSchedule(int i, String s, String s1, String s2, List<HistoricalSession> list) {

    }
}