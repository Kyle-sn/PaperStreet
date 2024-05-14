package com.paperstreet.strategy;

import com.opencsv.CSVParser;
import com.opencsv.CSVParserBuilder;
import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;
import com.opencsv.exceptions.CsvValidationException;

import java.io.FileReader;
import java.io.IOException;

public class StrategyUtils {

    /**
     * Counts the number of rows found in the day's position data file. For now, the assumption is that there will
     * only be positions in a single stock.
     *
     * @throws CsvValidationException
     * @throws IOException
     */
    public static int readPositionData() throws IOException, CsvValidationException {
        //TODO: dynamically populate which position file to read based on the current trade date.
        FileReader file = new FileReader("C:\\Users\\kylek\\data\\20240512_positionData.csv");

        CSVParser parser = new CSVParserBuilder()
                .withSeparator('|')
                .build();

        CSVReader reader = new CSVReaderBuilder(file)
                .withCSVParser(parser)
                .build();

        reader.skip(countCsvRows());
        String[] nextRecord = reader.readNext();
        String[] posEntry = nextRecord[2].split("=");

        return Integer.parseInt(posEntry[1]);
    }

    private static int countCsvRows() throws IOException, CsvValidationException {
        //TODO: dynamically populate which position file to read based on the current trade date.
        FileReader file = new FileReader("C:\\Users\\kylek\\data\\20240512_positionData.csv");

        CSVParser parser = new CSVParserBuilder()
                .withSeparator('|')
                .build();

        CSVReader reader = new CSVReaderBuilder(file)
                .withCSVParser(parser)
                .build();

        // count the number of rows in the csv being read
        int counter = 0;
        while (reader.readNext() != null) {
            counter++;
        }

        reader.close();
        file.close();
        // return the number of rows in the file minus one so we can then read the last row
        return counter - 1;
    }
}