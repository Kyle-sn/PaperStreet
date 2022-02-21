package com.paperstreet.strategy;

import java.io.*;

/**
 * Read in data that is being written by MarketDataReader to be used by strategy decisions.
 */
public class DataReader {

    /**
     * Read the last tick price that has been written to the csv created by the MarketDataWriter.
     *
     * @return the last recorded tick price.
     * @throws IOException
     */
    public static String readTicks() throws IOException {
        File file = new File("C:\\Users\\kylek\\Desktop\\ticks.csv");

        BufferedReader input = new BufferedReader(new FileReader(file));
        String last, line;

        String[] row = new String[0];
        while ((line = input.readLine()) != null) {
            last = line;
            row = last.split(",");
        }
        // current csv format:
        // time,symbol,price type,price
        System.out.println("Last price: " + row[3]);

        return row[3];
    }
}
