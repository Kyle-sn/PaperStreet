package com.paperstreet.positionhandler;

import com.ib.client.Decimal;

/**
 * Get and set position information returned from EWrapperImpl::updatePortfolio.
 */
public class Positions {

    private String symbol;
    private Decimal quantity;
    private double marketPrice;
    private double marketValue;
    private double averageCost;
    private double unrealizedPnl;
    private double realizedPnl;
    private String accountNumber;

    public Positions() {
    }

    public String getSymbol() {
        return symbol;
    }

    public void setSymbol(String symbol) {
        this.symbol = symbol;
    }

    public Decimal getQuantity() {
        return quantity;
    }

    public void setQuantity(Decimal quantity) {
        this.quantity = quantity;
    }

    public double getMarketPrice() {
        return marketPrice;
    }

    public void setMarketPrice(double marketPrice) {
        this.marketPrice = marketPrice;
    }

    public double getMarketValue() {
        return marketValue;
    }

    public void setMarketValue(double marketValue) {
        this.marketValue = marketValue;
    }

    public double getAverageCost() {
        return averageCost;
    }

    public void setAverageCost(double averageCost) {
        this.averageCost = averageCost;
    }

    public double getUnrealizedPnl() {
        return unrealizedPnl;
    }

    public void setUnrealizedPnl(double unrealizedPnl) {
        this.unrealizedPnl = unrealizedPnl;
    }

    public double getRealizedPnl() {
        return realizedPnl;
    }

    public void setRealizedPnl(double realizedPnl) {
        this.realizedPnl = realizedPnl;
    }

    public String getAccountNumber() {
        return accountNumber;
    }

    public void setAccountNumber(String accountNumber) {
        this.accountNumber = accountNumber;
    }

}

