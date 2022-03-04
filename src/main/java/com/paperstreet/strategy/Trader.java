package com.paperstreet.strategy;

import com.paperstreet.linehandler.OrderHandler;
import com.paperstreet.positionhandler.PositionHandler;

import java.util.concurrent.TimeUnit;

public class Trader {

    public static final OrderHandler orderHandler = new OrderHandler();
    public static final PositionHandler positionHandler = new PositionHandler();

    public static void main(String[] args) throws InterruptedException {
        // start up the position handler
        positionHandler.connectPositionHandler();
        positionHandler.requestAccountUpdates(true, "DU5231415");
        positionHandler.requestAccountSummary(6, "ALL");
        positionHandler.requestPositions();

        // start up the order handler
        orderHandler.connectOrderHandler();
        //TODO: improve the logic below so that we wait for a confirmed callback instead of sleeping
        TimeUnit.SECONDS.sleep(5);
        orderHandler.sendMarketOrder("QQQ", "BUY", 100);
    }
}
