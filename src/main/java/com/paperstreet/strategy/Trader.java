package com.paperstreet.strategy;

import com.paperstreet.orderhandler.OrderHandler;
import com.paperstreet.positionhandler.PositionChecker;
import com.paperstreet.positionhandler.PositionHandler;

import java.io.FileNotFoundException;
import java.util.Objects;
import java.util.concurrent.TimeUnit;

public class Trader {

    public static final OrderHandler orderHandler = new OrderHandler();
    public static final PositionHandler positionHandler = new PositionHandler();

    public static void main(String[] args) throws InterruptedException, FileNotFoundException {
        // start up the position handler
        positionHandler.connectPositionHandler();
        positionHandler.requestAccountUpdates(true, System.getenv("ACCOUNT_NUMBER"));
        positionHandler.requestAccountSummary(7, "ALL");
        positionHandler.requestPositions();

        // start up the order handler
        orderHandler.connectOrderHandler();

        // TODO: incorporate getPositionBalance to determine when to run placeTrade()
        PositionChecker.getPositionBalance();
        placeTrade();
    }

    private static void placeTrade() throws InterruptedException, FileNotFoundException {
        String signal = SignalReader.getSignal();
        if (Objects.equals(signal, "buy")) {
            TimeUnit.MINUTES.sleep(15);
            orderHandler.sendMarketOrder("QQQ", "BUY", 100);
        } else if (Objects.equals(signal, "sell")) {
            TimeUnit.MINUTES.sleep(15);
            orderHandler.sendMarketOrder("QQQ", "SELL", 100);
        }
    }
}
