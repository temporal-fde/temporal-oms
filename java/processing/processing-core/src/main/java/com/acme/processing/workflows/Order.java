package com.acme.processing.workflows;

import com.acme.proto.acme.apps.domain.apps.v1.*;
import com.acme.proto.acme.processing.domain.processing.v1.GetProcessOrderStateResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ProcessOrderRequest;
import io.temporal.workflow.*;

/**
 * Order Workflow - Processing Service
 *
 * Orchestrates order processing across the processing bounded context.
 * Uses UpdateWithStart pattern to accumulate data from commerce-app and payments-app webhooks.
 *
 * Workflow ID: order_id
 * Task Queue: processing
 * Namespace: processing
 */
@WorkflowInterface
public interface Order {

    @WorkflowMethod
    GetProcessOrderStateResponse execute(ProcessOrderRequest request);

    /**
     * Query: Get current order status
     */
    @QueryMethod
    GetProcessOrderStateResponse getState();
}