package com.acme.fulfillment.workflows;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.*;
import io.temporal.common.VersioningBehavior;
import io.temporal.workflow.*;

/**
 * fulfillment.Order Workflow
 *
 * Orchestrates the full post-processing fulfillment lifecycle: address verification,
 * inventory hold, carrier rate selection, label printing, inventory deduction, and
 * delivery status tracking.
 *
 * Workflow ID: order_id
 * Task Queue: fulfillment
 * Namespace: fulfillment
 * Versioning: PINNED
 *
 * Entry point: UpdateWithStart via the validateOrder Nexus operation from apps.Order.
 */
@WorkflowInterface
public interface Order {

    @WorkflowMethod
    void execute(StartOrderFulfillmentRequest request);

    /**
     * Update: Verify the shipping address via EasyPost.
     * Called by apps.Order via the validateOrder Nexus operation (UpdateWithStart).
     * Stores the verified Address (with easypost_address) in workflow state for
     * downstream use in ShippingAgent.calculateShippingOptions.
     */
    @UpdateMethod
    ValidateOrderResponse validateOrder(ValidateOrderRequest request);

    @UpdateValidatorMethod(updateName = "validateOrder")
    void validateValidateOrder(ValidateOrderRequest request);

    /**
     * Update: Proceed with fulfillment using the ProcessedOrder from processing.Order.
     * Sent by apps.Order after processOrder completes successfully.
     * Drives carrier rate selection, label printing, and inventory deduction.
     */
    @UpdateMethod
    FulfillOrderResponse fulfillOrder(FulfillOrderRequest request);

    @UpdateValidatorMethod(updateName = "fulfillOrder")
    void validateFulfillOrder(FulfillOrderRequest request);

    /**
     * Signal: Cancel the fulfillment order.
     * Triggers the detached compensation scope to release the inventory hold.
     */
    @SignalMethod
    void cancelOrder(CancelFulfillmentOrderRequest request);

    /**
     * Signal: Notify the workflow of a delivery status update from the carrier.
     * DELIVERED → complete workflow. CANCELED → notify customer, complete workflow.
     */
    @SignalMethod
    void notifyDeliveryStatus(NotifyDeliveryStatusRequest request);

    /**
     * Query: Return the current fulfillment order state.
     */
    @QueryMethod
    GetFulfillmentOrderStateResponse getState();
}
