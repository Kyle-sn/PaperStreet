package com.paperstreet.positionhandler;

/**
 * Class with main method used to connect the PositionHandler.
 */
public class ConnectPositionHandler {

    private static final PositionHandler positionHandler = new PositionHandler();

    /**
     * Connects the PositionHandler and then requests account and position information.
     * @param args
     */
    public static void main(String[] args) {
        positionHandler.connectPositionHandler();
        positionHandler.requestAccountUpdates(true, System.getenv("ACCOUNT_NUMBER"));
        positionHandler.requestAccountSummary(7, "ALL");
        positionHandler.requestPositions();
    }
}
