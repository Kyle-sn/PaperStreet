package com.paperstreet.positionhandler;

public class ConnectPositionHandler {

    private static final PositionHandler positionHandler = new PositionHandler();

    public static void main(String[] args) {
        positionHandler.connectPositionHandler();
        positionHandler.requestAccountUpdates(true, System.getenv("ACCOUNT_NUMBER"));
        positionHandler.requestAccountSummary(7, "ALL");
        positionHandler.requestPositions();
    }
}
