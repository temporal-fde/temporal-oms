package com.acme.apps.workflows;

import java.util.List;

/**
 * Warehouse with a pre-verified EasyPost address ID, held in Integrations workflow state.
 */
public record PreloadedWarehouse(
        String warehouseId,
        List<String> skuPrefixes,
        String easypostId,
        String company,
        String street1,
        String city,
        String state,
        String zip,
        String country
) {
    public PreloadedWarehouse(
            String warehouseId,
            List<String> skuPrefixes,
            String easypostId,
            String company,
            String street1,
            String street2,
            String city,
            String state,
            String zip,
            String country,
            boolean residential,
            double latitude,
            double longitude,
            String timezone) {
        this(warehouseId, skuPrefixes, easypostId, company, street1, city, state, zip, country);
    }
}
