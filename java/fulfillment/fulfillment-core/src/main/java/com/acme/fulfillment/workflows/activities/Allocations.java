package com.acme.fulfillment.workflows.activities;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.*;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

/**
 * Allocations activity — manages inventory hold, reservation, deduction, and release.
 *
 * holdItems: called in execute() after validateOrder to eagerly reserve stock.
 * reserveItems: called in fulfillOrder handler with warehouse-allocated items.
 * deductInventory: called after label is printed (concurrent with printShippingLabel).
 * releaseHold: called from the detached compensation scope on cancel or timeout.
 *
 * Phase 6: stub implementations return defaults; real integration deferred.
 */
@ActivityInterface
public interface Allocations {

    @ActivityMethod
    HoldItemsResponse holdItems(HoldItemsRequest request);

    @ActivityMethod
    ReserveItemsResponse reserveItems(ReserveItemsRequest request);

    @ActivityMethod
    DeductInventoryResponse deductInventory(DeductInventoryRequest request);

    @ActivityMethod
    ReleaseHoldResponse releaseHold(ReleaseHoldRequest request);
}
