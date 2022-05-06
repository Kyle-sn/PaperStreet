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
        File file = new File("C:\\Users\\kylek\\Desktop\\data\\" + date + "_marketData.csv");
        FileWriter writer = new FileWriter(file, true);

        StringBuilder builder = new StringBuilder();
        builder.append(LocalDateTime.now());
        builder.append(",");
        builder.append(marketData);
        System.out.println(builder);

        writer.write(builder.toString());
        writer.write(System.lineSeparator());
        writer.close();
    }

    public void parseOrderData(String orderData) throws IOException {
        String date = getDate();
        File file = new File("C:\\Users\\kylek\\Desktop\\data\\" + date + "_orderData.csv");
        FileWriter writer = new FileWriter(file, true);

        StringBuilder builder = new StringBuilder();
        builder.append(LocalDateTime.now());
        builder.append("|");
        builder.append(orderData);

        writer.write(builder.toString());
        writer.write(System.lineSeparator());
        writer.close();
    }

    public void parsePositionData(String positionData) throws IOException {
        String date = getDate();
        File file = new File("C:\\Users\\kylek\\Desktop\\data\\" + date + "_positionData.csv");
        FileWriter writer = new FileWriter(file, true);

        StringBuilder builder = new StringBuilder();
        builder.append(LocalDateTime.now());
        builder.append("|");
        builder.append(positionData);

        writer.write(builder.toString());
        writer.write(System.lineSeparator());
        writer.close();
    }

    public void parsePortfolioData(String portfolioData) throws IOException {
        String date = getDate();
        File file = new File("C:\\Users\\kylek\\Desktop\\data\\" + date + "_portfolioData.csv");
        FileWriter writer = new FileWriter(file, true);

        StringBuilder builder = new StringBuilder();
        builder.append(LocalDateTime.now());
        builder.append(",");
        builder.append(portfolioData);

        writer.write(builder.toString());
        writer.write(System.lineSeparator());
        writer.close();
    }

    public void parseOhlcData(String portfolioData) throws IOException {
        String date = getDate();
        File file = new File("C:\\Users\\kylek\\Desktop\\data\\" + date + "_ohlcData.csv");
        FileWriter writer = new FileWriter(file, true);

        StringBuilder builder = new StringBuilder();
        builder.append(LocalDateTime.now());
        builder.append(",");
        builder.append(portfolioData);

        writer.write(builder.toString());
        writer.write(System.lineSeparator());
        writer.close();
    }

    private String getDate() {
        LocalDate dateObj = LocalDate.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd");
        return dateObj.format(formatter);
    }
}