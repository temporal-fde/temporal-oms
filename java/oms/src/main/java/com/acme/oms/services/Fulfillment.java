package com.acme.oms.services;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.StartOrderFulfillmentRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ValidateOrderResponse;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

/**
 * Fulfillment Nexus service — exposes fulfillment.Order operations for cross-namespace callers.
 *
 * The validateOrder operation performs UpdateWithStart on fulfillment.Order with
 * WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING. The caller (apps.Order) provides the full
 * StartOrderFulfillmentRequest so the handler can both start the workflow (if needed)
 * and dispatch the validateOrder Update in a single call.
 *
 * Nexus endpoint name: order-fulfillment (registered in OMS properties, same pattern
 * as order-processing for apps.Order → processing.Order).
 */
@Service
public interface Fulfillment {

    @Operation
    ValidateOrderResponse validateOrder(StartOrderFulfillmentRequest request);
}
