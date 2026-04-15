package com.acme.fulfillment.workflows.activities;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

/**
 * Carriers activity — prints a shipping label using an EasyPost rate selection.
 *
 * printShippingLabel executes concurrently with Allocations.deductInventory in
 * the fulfillOrder handler; both are independent terminal operations.
 */
@ActivityInterface
public interface Carriers {

    @ActivityMethod
    PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request);
}
