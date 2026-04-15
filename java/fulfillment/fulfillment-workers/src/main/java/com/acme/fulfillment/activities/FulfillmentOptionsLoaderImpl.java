package com.acme.fulfillment.activities;

import com.acme.fulfillment.workflows.activities.FulfillmentOptionsLoader;
import com.acme.proto.acme.common.v1.Money;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FulfillmentOptions;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LoadFulfillmentOptionsRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * Stub implementation — returns a fixed shipping_margin of $10.00 (1000 cents).
 * Phase 6: replace with real config service / tenant-specific policy lookup.
 */
@Component("fulfillmentOptionsLoaderActivities")
public class FulfillmentOptionsLoaderImpl implements FulfillmentOptionsLoader {

    private static final Logger logger = LoggerFactory.getLogger(FulfillmentOptionsLoaderImpl.class);
    private static final long DEFAULT_SHIPPING_MARGIN_CENTS = 1000L; // $10.00

    @Override
    public FulfillmentOptions loadOptions(LoadFulfillmentOptionsRequest request) {
        logger.info("loadOptions stub: order_id={}, shipping_margin={}¢",
                request.getOrderId(), DEFAULT_SHIPPING_MARGIN_CENTS);

        return FulfillmentOptions.newBuilder()
                .setShippingMargin(Money.newBuilder()
                        .setCurrency("USD")
                        .setUnits(DEFAULT_SHIPPING_MARGIN_CENTS)
                        .build())
                .build();
    }
}
