package com.acme.oms.services;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.OrderFulfillRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.OrderFulfillResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.StartOrderFulfillmentRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ValidateOrderResponse;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

/**
 * Fulfillment Nexus service — exposes fulfillment.Order operations for cross-namespace callers.
 *
 * validateOrder performs UpdateWithStart on fulfillment.Order. fulfillOrder dispatches the
 * fulfillOrder Update to an already-running fulfillment.Order workflow (ACCEPTED stage only —
 * the Update is long-running and apps.Order does not need its result).
 *
 * Nexus endpoint name: order-fulfillment (registered in OMS properties, same pattern
 * as order-processing for apps.Order → processing.Order).
 */
@Service
public interface Fulfillment {

    @Operation
    ValidateOrderResponse validateOrder(StartOrderFulfillmentRequest request);

    @Operation
    OrderFulfillResponse fulfillOrder(OrderFulfillRequest request);
}
