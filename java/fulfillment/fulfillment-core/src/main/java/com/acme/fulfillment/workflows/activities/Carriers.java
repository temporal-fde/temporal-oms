package com.acme.fulfillment.workflows.activities;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

/**
 * Carriers activity — EasyPost address verification and label printing.
 *
 * verifyAddress: called in validateOrder Update handler; populates easypost_address.id.
 * printShippingLabel: called concurrently with InventoryService.deductInventory in fulfillOrder.
 *   Carrier rate selection is handled by the Python ShippingAgent (fulfillment-easypost task queue).
 */
@ActivityInterface
public interface Carriers {

    @ActivityMethod
    VerifyAddressResponse verifyAddress(VerifyAddressRequest request);

    @ActivityMethod
    PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request);
}
