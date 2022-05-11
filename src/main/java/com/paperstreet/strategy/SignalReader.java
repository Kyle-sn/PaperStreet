package com.paperstreet.strategy;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.Scanner;

public class SignalReader {

    private static String getSignal() throws FileNotFoundException {
        File file = new File("C:\\Users\\kylek\\Desktop\\data\\signal.csv");
        Scanner scanner = new Scanner(file);
        {
            while (scanner.hasNext()) {
                return scanner.next();
            }
        }
        return null;
    }
}