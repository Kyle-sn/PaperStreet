package com.paperstreet.trades;

import com.ib.client.Decimal;
import com.ib.client.Order;

/**
 * Different order types that we are able to send to IBKR.
 */
public class OrderTypes {

    /**
     * A Market order is an order to buy or sell at the market bid or offer price. A market order may increase
     * the likelihood of a fill and the speed of execution, but unlike the Limit order a Market order provides
     * no price protection and may fill at a price far lower/higher than the current displayed bid/ask.
     *
     * @param action Buy or Sell
     * @param quantity amount to trade
     * @return a market order
     */
    public static Order marketOrder(String action, int quantity) {
        Order order = new Order();
        order.action(action);
        order.orderType("MKT");
        order.totalQuantity(Decimal.get(quantity));
        return order;
    }

    /**
     * A Limit order is an order to buy or sell at a specified price or better. The Limit order ensures
     * that if the order fills, it will not fill at a price less favorable than your limit price,
     * but it does not guarantee a fill.
     *
     * @param action Buy or Sell
     * @param quantity amount to trade
     * @param limitPrice limit price
     * @return a limit order
     */
    public static Order limitOrder(String action, double quantity, double limitPrice) {
        Order order = new Order();
        order.action(action);
        order.orderType("LMT");
        order.totalQuantity(Decimal.get(quantity));
        order.lmtPrice(limitPrice);
        return order;
    }

    /**
     * A Stop order is an instruction to submit a buy or sell market order if and when the user-specified
     * stop trigger price is attained or penetrated. A Stop order is not guaranteed a specific execution
     * price and may execute significantly away from its stop price. A Sell Stop order is always placed
     * below the current market price and is typically used to limit a loss or protect a profit on a long
     * stock position. A Buy Stop order is always placed above the current market price. It is typically
     * used to limit a loss or help protect a profit on a short sale.
     *
     * @param action buy or sell
     * @param quantity amount to trade
     * @param stopPrice stop price
     * @return a stop order
     */
    public static Order stop(String action, double quantity, double stopPrice) {
        Order order = new Order();
        order.action(action);
        order.orderType("STP");
        order.auxPrice(stopPrice);
        order.totalQuantity(Decimal.get(quantity));
        return order;
    }

    /**
     * A Stop-Limit order is an instruction to submit a buy or sell limit order when the user-specified
     * stop trigger price is attained or penetrated. The order has two basic components: the stop price
     * and the limit price. When a trade has occurred at or through the stop price, the order becomes
     * executable and enters the market as a limit order, which is an order to buy or sell at a specified
     * price or better.
     *
     * @param action buy or sell
     * @param quantity amount to trade
     * @param limitPrice limit price
     * @param stopPrice stop price
     * @return stop limit order
     */
    public static Order stopLimit(String action, double quantity, double limitPrice, double stopPrice) {
        Order order = new Order();
        order.action(action);
        order.orderType("STP LMT");
        order.lmtPrice(limitPrice);
        order.auxPrice(stopPrice);
        order.totalQuantity(Decimal.get(quantity));
        return order;
    }

    /**
     * A sell trailing stop order sets the stop price at a fixed amount below the market price with an
     * attached "trailing" amount. As the market price rises, the stop price rises by the trail amount,
     * but if the stock price falls, the stop loss price doesn't change, and a market order is submitted
     * when the stop price is hit. This technique is designed to allow an investor to specify a limit on
     * the maximum possible loss, without setting a limit on the maximum possible gain. "Buy" trailing
     * stop orders are the mirror image of sell trailing stop orders, and are most appropriate for use
     * in falling markets.
     *
     * Note that Trailing Stop orders can have the trailing amount specified as a percent, or as an
     * absolute amount which is specified in the auxPrice field.
     *
     * @param action buy or sell
     * @param quantity amount to trade
     * @param trailingPercent trailing amount specified as a percent
     * @param trailStopPrice trailing stop price
     * @return a trailing stop market order
     */
    public static Order trailingStop(String action, double quantity, double trailingPercent, double trailStopPrice) {
        Order order = new Order();
        order.action(action);
        order.orderType("TRAIL");
        order.trailingPercent(trailingPercent);
        order.trailStopPrice(trailStopPrice);
        order.totalQuantity(Decimal.get(quantity));
        return order;
    }
}
