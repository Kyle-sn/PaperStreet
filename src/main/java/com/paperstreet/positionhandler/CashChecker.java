package com.paperstreet.positionhandler;

public class CashChecker {

    private static double cashBalance;

    public static void setCashBalance(String cashStr) {
        CashChecker.cashBalance = Double.parseDouble(cashStr);
    }

    public static double getCashBalance() {
        return cashBalance;
    }
}
