package com.paperstreet.utils;

import java.time.LocalDateTime;

public class LogHandler {

    public void logInfo(String message) {
        StackTraceElement l = new Exception().getStackTrace()[1];
        System.out.println(LocalDateTime.now() +
                " INFO [" +
                l.getClassName() + "/" +
                l.getMethodName() + "." +
                l.getLineNumber() + "]: " +
                message);
    }

    public void logError(String message) {
        StackTraceElement l = new Exception().getStackTrace()[1];
        System.out.println(LocalDateTime.now() +
                " ERROR [" +
                l.getClassName() + "/" +
                l.getMethodName() + "." +
                l.getLineNumber() + "]: " +
                message);
    }
}
