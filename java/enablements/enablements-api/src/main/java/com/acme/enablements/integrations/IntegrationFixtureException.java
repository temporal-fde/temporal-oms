package com.acme.enablements.integrations;

public class IntegrationFixtureException extends RuntimeException {

    public enum Code {
        ADDRESS_VERIFY_FAILED,
        BAD_REQUEST,
        INVALID_RATE,
        UNKNOWN_ADDRESS,
        UNKNOWN_SHIPMENT
    }

    private final Code code;

    public IntegrationFixtureException(Code code, String message) {
        super(message);
        this.code = code;
    }

    public Code getCode() {
        return code;
    }
}
