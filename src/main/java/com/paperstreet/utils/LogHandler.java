package com.paperstreet.utils;

import java.time.LocalDateTime;

/**
 * Custom log handler.
 */
public class LogHandler {

    /**
     * Logs a line for basic informational purposes.
     * @param message
     */
    public void logInfo(String message) {
        StackTraceElement l = new Exception().getStackTrace()[1];
        System.out.println(LocalDateTime.now() +
                " INFO [" +
                l.getClassName() + "/" +
                l.getMethodName() + "." +
                l.getLineNumber() + "]: " +
                message);
    }

    /**
     * Logs a line for errors.
     * @param message
     */
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
