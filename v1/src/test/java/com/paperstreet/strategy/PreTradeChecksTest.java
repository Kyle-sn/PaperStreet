package com.paperstreet.strategy;

import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mockStatic;

class PreTradeChecksTest {
    String signalSideBuy = "BUY";
    String signalSideSell = "SELL";
    int quantity = 1000;
    int strategyId = 123;
    int maxPos = 1000;

    @Test
    void testAdjustQuantityDirection() {
        assertEquals(-1000, PreTradeChecks.adjustQuantityDirection(quantity, signalSideSell));
        assertEquals(1000, PreTradeChecks.adjustQuantityDirection(quantity, signalSideBuy));
    }

    @Test
    public void testCheckValidTradeSize_withinLimit() {
        int quantity = 100;
        int strategyId = 1;

        // Mocking the readMaxPosParameter method
        try (MockedStatic<StrategyParameterReader> mockedStrategyParameterReader = mockStatic(StrategyParameterReader.class)) {
            mockedStrategyParameterReader.when(() ->
                            StrategyParameterReader.getParam("max_pos", strategyId)).thenReturn(maxPos);

            boolean result = PreTradeChecks.checkValidTradeSize(quantity, strategyId);

            assertTrue(result, "Trade size should be valid when within the limit");
        }
    }

    @Test
    public void testCheckValidTradeSize_exceedsLimit() {
        int quantity = 1500; // Example quantity exceeding the limit
        int strategyId = 1;

        try (MockedStatic<StrategyParameterReader> mockedStrategyParameterReader = mockStatic(StrategyParameterReader.class)) {
            mockedStrategyParameterReader.when(() -> StrategyParameterReader.getParam("max_pos", strategyId)).thenReturn(maxPos);

            boolean result = PreTradeChecks.checkValidTradeSize(quantity, strategyId);

            assertFalse(result, "Trade size should be invalid when exceeding the limit");
        }
    }

    @Test
    public void testPassedPreTradeChecks() {
        int quantity = 500; // Example quantity within the limit
        boolean canShort = true;

        // Mocking static methods and other dependencies
        try (MockedStatic<StrategyParameterReader> mockedStrategyParameterReader = mockStatic(StrategyParameterReader.class);
             MockedStatic<StrategyUtils> mockedStrategyUtils = mockStatic(StrategyUtils.class)) {

            mockedStrategyParameterReader.when(() -> StrategyParameterReader.getParam("can_short", strategyId)).thenReturn(canShort);
            mockedStrategyParameterReader.when(() -> StrategyParameterReader.getParam("max_pos", strategyId)).thenReturn(maxPos);
            mockedStrategyUtils.when(StrategyUtils::readPositionData).thenReturn(50);

            boolean result = PreTradeChecks.passedPreTradeChecks(strategyId, signalSideBuy, quantity);

            assertTrue(result, "Pre trade checks should pass with valid conditions");
        }
    }

    @Test
    public void testPassedPreTradeChecks_invalidTradeSize() {
        int quantity = 1500; // Example quantity exceeding the limit
        boolean canShort = true;

        // Mocking static methods and other dependencies
        try (MockedStatic<StrategyParameterReader> mockedStrategyParameterReader = mockStatic(StrategyParameterReader.class);
             MockedStatic<StrategyUtils> mockedStrategyUtils = mockStatic(StrategyUtils.class)) {

            mockedStrategyParameterReader.when(() -> StrategyParameterReader.getParam("can_short", strategyId)).thenReturn(canShort);
            mockedStrategyParameterReader.when(() -> StrategyParameterReader.getParam("max_pos", strategyId)).thenReturn(maxPos);
            mockedStrategyUtils.when(StrategyUtils::readPositionData).thenReturn(50);

            boolean result = PreTradeChecks.passedPreTradeChecks(strategyId, signalSideSell, quantity);

            assertFalse(result, "Pre trade checks should fail with invalid trade size");
        }
    }
}