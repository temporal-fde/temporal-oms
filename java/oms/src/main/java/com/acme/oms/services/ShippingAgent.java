package com.acme.oms.services;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.CalculateShippingOptionsRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.CalculateShippingOptionsResponse;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

/**
 * ShippingAgent Nexus service — exposes the Python ShippingAgent workflow for cross-namespace callers.
 *
 * calculateShippingOptions performs UpdateWithStart on the ShippingAgent workflow (WorkflowID = customer_id)
 * via the Python Nexus handler in the fulfillment namespace on the "agents" task queue.
 *
 * Nexus endpoint name: shipping-agent (registered in acme.oms.yaml and Temporal cluster).
 */
@Service
public interface ShippingAgent {

    @Operation
    CalculateShippingOptionsResponse calculateShippingOptions(CalculateShippingOptionsRequest request);
}
