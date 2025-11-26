package com.paperstreet.marketdata;

import com.ib.client.Contract;
import com.paperstreet.utils.LogHandler;

import static com.paperstreet.marketdata.MarketDataConstants.*;

/**
 * Class for the creation of an IBKR contract to be traded.
 */
public class ContractHandler {

    private static final LogHandler logHandler = new LogHandler();

    /**
     * Converts the provided symbol to a valid IBKR contract. The contract helps identify and route
     * market data requests to the broker specifying the security type, exchange, and currency of US stocks.
     *
     * @param ticker The symbol to convert to a valid contract.
     * @return A contract associated with the symbol.
     */
    public static Contract contract(String ticker) {
        Contract contract = new Contract();
        contract.symbol(ticker);
        contract.secType(SECURITY_TYPE);
        contract.exchange(EXCHANGE);
        contract.currency(CURRENCY);

        logHandler.logInfo("Contract created for " + ticker);
        return contract;
    }

    public static Contract getContract(String symbol) {
        return contract(symbol);
    }
}
