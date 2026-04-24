package com.acme.fulfillment.workflows.activities;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetCarrierRatesRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetCarrierRatesResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

/**
 * Carriers activity — all EasyPost shipping operations consolidated.
 *
 * verifyAddress: called in validateOrder Update handler; populates easypost_address.id.
 * getCarrierRates: called in fulfillOrder handler; creates EasyPost Shipment + queries rates (V1).
 * printShippingLabel: called concurrently with InventoryService.deductInventory in fulfillOrder.
 */
@ActivityInterface
public interface Carriers {

    @ActivityMethod
    VerifyAddressResponse verifyAddress(VerifyAddressRequest request);

    @ActivityMethod
    GetCarrierRatesResponse getCarrierRates(GetCarrierRatesRequest request);

    @ActivityMethod
    PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request);
}
