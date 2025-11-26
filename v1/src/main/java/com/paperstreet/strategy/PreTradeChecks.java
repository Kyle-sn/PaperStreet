package com.paperstreet.strategy;

import com.opencsv.exceptions.CsvValidationException;
import com.paperstreet.utils.LogHandler;

import java.io.IOException;

/**
 * Perform various checks prior to submitting a trade to make sure trades adhere to predefined logic.
 */
public class PreTradeChecks {
    private static final LogHandler logHandler = new LogHandler();
    static int posSize;

    /**
     * Bool to confirm whether or not checks have been passed.
     *
     * @param strategyId ID of the strategy placing a trade
     * @param signalSide side of the trade (buy/sell)
     * @param quantity size of the trade
     * @return true or false based on the result of the checks being passed or not
     */
    public static boolean passedPreTradeChecks(int strategyId, String signalSide, int quantity) {
        quantity = adjustQuantityDirection(quantity, signalSide);

        boolean canShort = canShort(strategyId);
        boolean isTryingToShort = checkIfTryingToShort(quantity);
        boolean tradeSizeIsValid = checkValidTradeSize(quantity, strategyId);

        return (tradeSizeIsValid && canShort && isTryingToShort) ||
                (tradeSizeIsValid && !isTryingToShort);
    }

    /**
     * A check to make sure a strategy is configured to short.
     *
     * @param strategyId ID of the strategy placing a trade
     * @return
     */
    public static boolean canShort(int strategyId) {
        Object canShortObj = StrategyParameterReader.getParam("can_short", strategyId);
        assert canShortObj != null;
        return (boolean) canShortObj;
    }

    public static boolean checkIfTryingToShort(int quantity) {
        try {
            posSize = StrategyUtils.readPositionData();
        } catch (CsvValidationException | IOException e) {
            throw new RuntimeException(e);
        }

        // According to IBKR "For general account types, a SELL order will be able to enter a short position
        // automatically if the order quantity is larger than your current long position."
        int quantityAfterTrade = posSize - quantity;
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
