package com.paperstreet.strategy;

import com.paperstreet.orderhandler.OrderHandler;
import com.paperstreet.positionhandler.CashChecker;
import com.paperstreet.positionhandler.PositionChecker;
import com.paperstreet.positionhandler.PositionHandler;
import com.paperstreet.utils.LogHandler;

import java.io.FileNotFoundException;
import java.util.Objects;
import java.util.concurrent.TimeUnit;

public class Trader {

    public static final OrderHandler orderHandler = new OrderHandler();
    public static final PositionHandler positionHandler = new PositionHandler();
    public static final LogHandler logHandler = new LogHandler();

    public static void main(String[] args) throws InterruptedException, FileNotFoundException {
        // start up the position handler
        positionHandler.connectPositionHandler();
        positionHandler.requestAccountUpdates(true, System.getenv("ACCOUNT_NUMBER"));
        positionHandler.requestAccountSummary(7, "ALL");
        positionHandler.requestPositions();

        // start up the order handler
        orderHandler.connectOrderHandler();

        placeTrade();
    }

    private static void placeTrade() throws InterruptedException, FileNotFoundException {
        TimeUnit.SECONDS.sleep(5);
        String signal = SignalReader.getSignal();
        boolean hasPositionBalance = PositionChecker.getPositionBalanceBool();

        if (Objects.equals(signal, "buy")) {
            if (hasPositionBalance) {
                logHandler.logError("Todays signal is to BUY but we already have a position.");
            } else if (!hasPositionBalance) {
                TimeUnit.MINUTES.sleep(15);

                double sharePrice = PositionChecker.getSharePrice();
                double cashBalance = CashChecker.getCashBalance();
                double qtyToBuy = Math.floor(cashBalance / sharePrice);

                orderHandler.sendMarketOrder("QQQ", "BUY", qtyToBuy);
            }
        } else if (Objects.equals(signal, "sell")) {
            if (!hasPositionBalance) {
                logHandler.logError("Todays signal is to SELL but we do not have any positions to sell");
            } else if (hasPositionBalance) {
                TimeUnit.MINUTES.sleep(15);

                double qtyToSell = PositionChecker.getPositionShareCount();

                orderHandler.sendMarketOrder("QQQ", "SELL", qtyToSell);
            }
        }
    }
}
