package com.paperstreet.positionhandler;

import com.ib.client.Decimal;

public class PositionChecker {

    private static boolean currentlyHaveAPosition;
    private static double currentShareCount;
    private static double sharePrice;

    public static void setSharePrice(double price) {
        PositionChecker.sharePrice = price;
    }

    public static double getSharePrice() {
        return sharePrice;
    }

    public static void setPositionShareCount(Decimal position) {
        String positionStr = position.toString();
        PositionChecker.currentShareCount = Double.parseDouble(positionStr);
    }

    public static double getPositionShareCount() {
        return currentShareCount;
    }

    public static void setPositionBalanceBool() {
        if (currentShareCount != 0) {
            PositionChecker.currentlyHaveAPosition = true;
        } else if (currentShareCount == 0){
            PositionChecker.currentlyHaveAPosition = false;
        }
    }

    public static boolean getPositionBalanceBool() {
        setPositionBalanceBool();
        return currentlyHaveAPosition;
    }
}
