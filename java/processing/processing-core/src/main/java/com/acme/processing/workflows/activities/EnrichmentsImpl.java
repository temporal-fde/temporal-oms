package com.acme.processing.workflows.activities;

import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderResponse;
import org.springframework.stereotype.Component;

@Component("enrichment-activities")
public class EnrichmentsImpl implements Enrichments {
    @Override
    public EnrichOrderResponse enrichOrder(EnrichOrderRequest cmd) {
        // 1. load order from db
        // 2. call pim service with item ids to get details
        // 3. map sku and brand_code to each item
        // return enriched items
        return EnrichOrderResponse.getDefaultInstance();
    }
}
