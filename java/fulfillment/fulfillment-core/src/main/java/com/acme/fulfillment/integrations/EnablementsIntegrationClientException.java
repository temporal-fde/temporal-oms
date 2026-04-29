package com.acme.fulfillment.integrations;

public class EnablementsIntegrationClientException extends RuntimeException {

    private final int statusCode;
    private final String errorCode;

    public EnablementsIntegrationClientException(int statusCode, String errorCode, String message, Throwable cause) {
        super(message, cause);
        this.statusCode = statusCode;
        this.errorCode = errorCode;
    }

    public int getStatusCode() {
        return statusCode;
    }

    public String getErrorCode() {
        return errorCode;
    }
}
