package strategy;

import linehandler.OrderHandler;

import java.util.concurrent.TimeUnit;

public class Trader {
    //TODO: add logic to send a limit order within x% of the last price written by MarketDataHandler
    public static final OrderHandler orderHandler = new OrderHandler();

    public static void main(String[] args) throws InterruptedException {
        orderHandler.connectOrderHandler();
        //TODO: improve the logic below so that we wait for a confirmed callback instead of sleeping
        TimeUnit.SECONDS.sleep(5);
        orderHandler.sendLimitOrder("NQ", "BUY", 1, 14050);
    }
}
