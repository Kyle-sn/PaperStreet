package com.paperstreet.positionhandler;

import com.ib.client.Decimal;

/**
 * Get and set position information returned from EWrapperImpl::updatePortfolio.
 */
public class Positions {

    private String symbol;
    private Decimal quantity;
    private double averageCost;
    private String accountNumber;

    /**
     * Class for creating position objects.
     */
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

    public double getAverageCost() {
        return averageCost;
    }

    public void setAverageCost(double averageCost) {
        this.averageCost = averageCost;
    }

    public String getAccountNumber() {
        return accountNumber;
    }

    public void setAccountNumber(String accountNumber) {
        this.accountNumber = accountNumber;
    }

}

