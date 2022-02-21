package com.paperstreet.marketdata;

import com.ib.client.Contract;

import static com.paperstreet.marketdata.MarketDataConstants.*;

public class ContractHandler {

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
        contract.localSymbol("NQH2"); // remove when done testing using futures, only care about stocks
        contract.secType(SECURITY_TYPE);
        contract.exchange(EXCHANGE);
        contract.currency(CURRENCY);

        return contract;
    }

    public static Contract getContract(String symbol) {
        return contract(symbol);
    }
}
