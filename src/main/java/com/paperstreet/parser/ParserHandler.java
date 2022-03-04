package com.paperstreet.parser;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;

/**
 * Write callbacks received from EWrapperImpl to a csv.
 */
public class ParserHandler {

    public void parseMarketData(String marketData) throws IOException {
        File file = new File("C:\\Users\\kylek\\Desktop\\marketData.csv");
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
        File file = new File("C:\\Users\\kylek\\Desktop\\orderData.csv");
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
        File file = new File("C:\\Users\\kylek\\Desktop\\positionData.csv");
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
        File file = new File("C:\\Users\\kylek\\Desktop\\portfolioData.csv");
        FileWriter writer = new FileWriter(file, true);

        StringBuilder builder = new StringBuilder();
        builder.append(LocalDateTime.now());
        builder.append(",");
        builder.append(portfolioData);

        writer.write(builder.toString());
        writer.write(System.lineSeparator());
        writer.close();
    }
}