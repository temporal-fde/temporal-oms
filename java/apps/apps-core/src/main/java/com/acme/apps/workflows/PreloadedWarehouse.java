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
) {}
