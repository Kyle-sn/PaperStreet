package com.paperstreet.strategy;

import com.opencsv.exceptions.CsvValidationException;
import com.paperstreet.utils.LogHandler;

import java.io.IOException;

public class PreTradeChecks {
    private static final LogHandler logHandler = new LogHandler();
    static int posSize;

    public static boolean passedPreTradeChecks(int strategyId, String signalSide, int quantity) {
        quantity = adjustQuantityDirection(quantity, signalSide);

        Object canShortObj = StrategyParameterReader.getParam("can_short", strategyId);
        assert canShortObj != null;
        boolean canShort = (boolean) canShortObj;
        boolean isTryingToShort = checkIfTryingToShort(quantity);
        boolean tradeSizeIsValid = checkValidTradeSize(quantity, strategyId);

        return (tradeSizeIsValid && canShort && isTryingToShort) ||
                (tradeSizeIsValid && !isTryingToShort);
    }

    public static boolean checkIfTryingToShort(int quantity) {
        try {
            posSize = StrategyUtils.readPositionData();
        } catch (CsvValidationException | IOException e) {
            throw new RuntimeException(e);
        }

        // According to IBKR "For general account types, a SELL order will be able to enter a short position
        // automatically if the order quantity is larger than your current long position."
        int quantityAfterTrade = quantity - posSize;
        return quantityAfterTrade < 0;
    }

    public static boolean checkValidTradeSize(int quantity, int strategyId) {
        int maxPos = readMaxPosParameter(strategyId);

        if (Math.abs(quantity) <= maxPos) {
            return true;
        }

        logHandler.logError("Error placing trade. Trade quantity of " + quantity +
                " is greater than the configured max position limit of " + maxPos);
        return false;
    }

    public static int readMaxPosParameter(int strategyId) {
        Object maxPosObj = StrategyParameterReader.getParam("max_pos", strategyId);
        assert maxPosObj != null;
        return (int) maxPosObj;
    }

    public static int adjustQuantityDirection(int quantity, String signalSide) {
        if (signalSide.equals("SELL")) {
            return quantity * -1;
        }
        return quantity;
    }
}
