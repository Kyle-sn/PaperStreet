package com.paperstreet.strategy;

import com.paperstreet.linehandler.OrderHandler;
import com.paperstreet.positionhandler.PositionHandler;

public class Trader {

    public static final OrderHandler orderHandler = new OrderHandler();
    public static final PositionHandler positionHandler = new PositionHandler();

    public static void main(String[] args) {
        // start up the position handler
        positionHandler.connectPositionHandler();
        positionHandler.requestAccountUpdates(true, "DU5231415");
        positionHandler.requestAccountSummary(6, "ALL");
        positionHandler.requestPositions();

        // start up the order handler
        orderHandler.connectOrderHandler();
        orderHandler.sendMarketOrder("QQQ", "BUY", 100);
    }
}
