package com.acme.fulfillment.workflows.activities;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FulfillmentOptions;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LoadFulfillmentOptionsRequest;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

/**
 * FulfillmentOptionsLoader local activity — loads fulfillment policy in-process.
 *
 * Runs as a LocalActivity (no task queue round-trip) immediately after execute() starts.
 * Loads shipping_margin from config or a config service. The margin is used in the
 * fulfillOrder handler to detect and record margin leakage.
 */
@ActivityInterface
public interface FulfillmentOptionsLoader {

    @ActivityMethod
    FulfillmentOptions loadOptions(LoadFulfillmentOptionsRequest request);
}
