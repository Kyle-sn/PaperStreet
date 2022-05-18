package com.paperstreet.positionhandler;

import com.ib.client.Decimal;

public class PositionChecker {

    private static boolean currentlyHaveAPosition;

    public static void setPositionBalanceBool(Decimal position) {
        if (!position.isZero()) {
            PositionChecker.currentlyHaveAPosition = true;
        } else if (position.isZero()){
            PositionChecker.currentlyHaveAPosition = false;
        }
    }

    public static boolean getPositionBalance() {
        return currentlyHaveAPosition;
    }
}
