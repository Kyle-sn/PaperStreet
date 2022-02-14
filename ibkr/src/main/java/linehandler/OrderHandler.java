package linehandler;

import com.ib.client.Contract;
import com.ib.client.EClient;
import marketdata.ContractHandler;

import java.time.LocalDateTime;

// called by the strategy
// sends an order to the broker using one of the orders found in OrderTypes
public class OrderHandler {

    private static EClient client = null;
    private static int nextValidID = 0;

    public OrderHandler(EClient client) {
        OrderHandler.client = client;
    }

    public static void sendLimitOrder(String symbol, String side, double quantity, double price) {
        Contract contract = ContractHandler.getContract(symbol);
        client.placeOrder(getNextValidId(),
                contract,
                OrderTypes.LimitOrder(side, quantity, price));

        LocalDateTime timeStamp = LocalDateTime.now();

        System.out.println(timeStamp + ": order=limit_order,side=" + side + ",quantity=" + quantity + ",symbol=" + symbol + ",price=" + price);
    }

    // NextValidId setter
    public static void setNextValidId(int nextValidID) {
        OrderHandler.nextValidID = nextValidID;
    }

    // NextValidId getter
    public static int getNextValidId() {
        nextValidID++;
        return nextValidID;
    }

    // still need to tweak this, but need something like this if I am going to submit
    // a buy/sell with a stop loss, i.e. buy order gets nextValidId++ while the stop
    // loss gets nextValidId+=2.
    public static int getNextValidIdOrder() {
        nextValidID+=2  ;
        return nextValidID;
    }
}
