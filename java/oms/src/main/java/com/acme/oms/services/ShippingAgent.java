package com.acme.oms.services;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.RecommendShippingOptionRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.RecommendShippingOptionResponse;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

/**
 * ShippingAgent Nexus service — exposes the Python ShippingAgent workflow for cross-namespace callers.
 *
 * recommendShippingOption performs UpdateWithStart on the ShippingAgent workflow (WorkflowID = customer_id)
 * via the Python Nexus handler in the fulfillment namespace on the "agents" task queue.
 *
 * Nexus endpoint name: shipping-agent (registered in acme.oms.yaml and Temporal cluster).
 */
@Service
public interface ShippingAgent {

    @Operation
    RecommendShippingOptionResponse recommendShippingOption(RecommendShippingOptionRequest request);
}
