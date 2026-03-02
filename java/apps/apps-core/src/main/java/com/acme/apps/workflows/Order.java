package com.acme.apps.workflows;

import com.acme.proto.acme.apps.domain.apps.v1.*;

import io.temporal.workflow.QueryMethod;
import io.temporal.workflow.UpdateMethod;
import io.temporal.workflow.UpdateValidatorMethod;
import io.temporal.workflow.WorkflowInterface;
import io.temporal.workflow.WorkflowMethod;

/**
 * CompleteOrder Workflow - Application Service
 *
 * Orchestrates order completion across multiple namespaces using Nexus.
 * Uses UpdateWithStart pattern to accumulate data from commerce-app and payments-app webhooks.
 *
 * Workflow ID: order_id
 * Task Queue: apps
 * Namespace: apps
 */
@WorkflowInterface
public interface Order {

    @WorkflowMethod
    void execute(CompleteOrderRequest request);

    /**
     * Update: Submit commerce data from commerce-app webhook
     * Uses UpdateWithStart to accumulate data
     */
    @UpdateMethod
    GetCompleteOrderStateResponse submitOrder(SubmitOrderRequest request);

    @UpdateValidatorMethod(updateName = "submitOrder")
    void validateSubmitOrder(SubmitOrderRequest request);

    /**
     * Update: Submit payment data from payments-app webhook
     * Uses UpdateWithStart to accumulate data
     */
    @UpdateMethod
    GetCompleteOrderStateResponse capturePayment(CapturePaymentRequest request);

    @UpdateValidatorMethod(updateName = "capturePayment")
    void validateCapturePayment(CapturePaymentRequest request);

    /**
     * Update: Cancel order
     * Can be cancelled up to 30 days or until payment is completed
     */
    @UpdateMethod
    CancelOrderResponse cancelOrder(CancelOrderRequest request);

    @UpdateValidatorMethod(updateName = "cancelOrder")
    void validateCancelOrder(CancelOrderRequest request);

    /**
     * Query: Get current order status
     */
    @QueryMethod
    GetCompleteOrderStateResponse getState();
}