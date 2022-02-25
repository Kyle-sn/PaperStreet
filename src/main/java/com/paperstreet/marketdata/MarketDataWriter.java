package com.paperstreet.marketdata;

import java.io.*;
import java.time.LocalDateTime;

public class MarketDataWriter {

    /**
     * Write each tick callback received from EWrapperImpl to a csv.
     *
     * @param timeStamp time when callback was received.
     * @param symbol symbol that the market data relates to.
     * @param field the TickType that is being saved.
     * @param price the price associated with the TickType being saved.
     * @throws IOException
     */
    public void writeTicks(LocalDateTime timeStamp, String symbol, String field, double price) throws IOException {
        File file = new File("C:\\Users\\kylek\\Desktop\\ticks.csv");
        FileWriter writer = new FileWriter(file, true);

        StringBuilder builder = new StringBuilder();
        builder.append(timeStamp);
        builder.append(",");
        builder.append(symbol.toLowerCase());
        builder.append(",");
        builder.append(field);
        builder.append(",");
        builder.append(price);
        System.out.println(builder);

        writer.write(builder.toString());
        writer.write(System.lineSeparator());
        writer.close();
    }
}
