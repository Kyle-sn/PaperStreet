package com.paperstreet.parser;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Write callbacks received from EWrapperImpl to a csv.
 */
public class ParserHandler {

    public void parseMarketData(String marketData) throws IOException {
        String date = getDate();
        File file = new File("C:\\Users\\kylek\\data\\" + date + "_marketData.csv");
        FileWriter writer = new FileWriter(file, true);

        String marketDataWithDate = LocalDateTime.now() + "," + marketData;

        writer.write(marketDataWithDate);
        writer.write(System.lineSeparator());
        writer.close();
    }

    public void parseTickSizeData(String marketData) throws IOException {
        String date = getDate();
        File file = new File("C:\\Users\\kylek\\data\\" + date + "_tickSizeData.csv");
        FileWriter writer = new FileWriter(file, true);

        String tickSizeDataWithDate = LocalDateTime.now() + "," + marketData;

        writer.write(tickSizeDataWithDate);
        writer.write(System.lineSeparator());
        writer.close();
    }

    public void parseOrderData(String orderData) throws IOException {
        String date = getDate();
        File file = new File("C:\\Users\\kylek\\data\\" + date + "_orderData.csv");
        FileWriter writer = new FileWriter(file, true);

        String orderDataWithDate = LocalDateTime.now() + "|" + orderData;

        writer.write(orderDataWithDate);
        writer.write(System.lineSeparator());
        writer.close();
    }

    public void parsePositionData(String positionData) throws IOException {
        String date = getDate();
        File file = new File("C:\\Users\\kylek\\data\\" + date + "_positionData.csv");
        FileWriter writer = new FileWriter(file, true);

        String positionDataWithDate = LocalDateTime.now() + "|" + positionData;

        writer.write(positionDataWithDate);
        writer.write(System.lineSeparator());
        writer.close();
    }

    public void parsePortfolioData(String portfolioData) throws IOException {
        String date = getDate();
        File file = new File("C:\\Users\\kylek\\data\\" + date + "_portfolioData.csv");
        FileWriter writer = new FileWriter(file, true);

        String portfolioDataWithDate = LocalDateTime.now() + "," + portfolioData;

        writer.write(portfolioDataWithDate);
        writer.write(System.lineSeparator());
        writer.close();
    }

    public void parseOhlcData(String portfolioData) throws IOException {
        String date = getDate();
        File file = new File("C:\\Users\\kylek\\data\\" + date + "_ohlcData.csv");
        FileWriter writer = new FileWriter(file, true);

        String ohlcDataWithDate = LocalDateTime.now() + "," + portfolioData;

        writer.write(ohlcDataWithDate);
        writer.write(System.lineSeparator());
        writer.close();
    }

    private String getDate() {
        LocalDate dateObj = LocalDate.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd");
        return dateObj.format(formatter);
    }
}