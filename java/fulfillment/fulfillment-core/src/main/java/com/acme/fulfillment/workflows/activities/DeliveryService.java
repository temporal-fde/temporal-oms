package com.acme.fulfillment.workflows.activities;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetCarrierRatesRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetCarrierRatesResponse;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

/**
 * DeliveryService activity (V1 shipping path) — queries carrier rates via EasyPost.
 *
 * Creates an EasyPost Shipment using the verified easypost_address_id (stored from
 * validateOrder) and the ProcessedOrder items, then returns the available carrier rates.
 * The shipment_id in the response is passed to Carriers.printShippingLabel.
 *
 * V2 path (ShippingAgent via Nexus) is deferred to Phase 7.
 */
@ActivityInterface
public interface DeliveryService {

    @ActivityMethod
    GetCarrierRatesResponse getCarrierRates(GetCarrierRatesRequest request);
}
