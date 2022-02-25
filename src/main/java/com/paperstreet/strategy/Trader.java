package com.paperstreet.strategy;

import com.paperstreet.linehandler.OrderHandler;

import java.util.concurrent.TimeUnit;

public class Trader {

    public static final OrderHandler orderHandler = new OrderHandler();

    public static void main(String[] args) throws InterruptedException {
        orderHandler.connectOrderHandler();
        //TODO: improve the logic below so that we wait for a confirmed callback instead of sleeping
        TimeUnit.SECONDS.sleep(5);
        orderHandler.sendLimitOrder("QQQ", "BUY", 1, 330.00);
    }
}