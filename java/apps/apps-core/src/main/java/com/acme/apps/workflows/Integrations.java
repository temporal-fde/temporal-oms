package com.acme.apps.workflows;

import com.acme.proto.acme.apps.domain.apps.v1.StartIntegrationsRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressResponse;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ValidatePaymentRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidatePaymentResponse;
import io.temporal.workflow.*;

/**
 * apps.Integrations Workflow
 *
 * Singleton in-memory integration stub for workshop use.
 * All external service calls (CommerceApp, PIMS, Payments, Inventory) route
 * here via UpdateWithStart from their respective Nexus service handlers.
 *
 * Workflow ID: "integrations" | Task Queue: apps | Namespace: apps
 * Versioning: PINNED
 */
@WorkflowInterface
public interface Integrations {

    @WorkflowMethod
    void execute(StartIntegrationsRequest request);

    // ── CommerceApp ───────────────────────────────────────────────────────────

    @UpdateMethod
    ValidateOrderResponse validateOrder(ValidateOrderRequest request);

    @UpdateValidatorMethod(updateName = "validateOrder")
    void validateValidateOrder(ValidateOrderRequest request);

    // ── PIMS ──────────────────────────────────────────────────────────────────

    @UpdateMethod
    EnrichOrderResponse enrichOrder(EnrichOrderRequest request);

    @UpdateValidatorMethod(updateName = "enrichOrder")
    void validateEnrichOrder(EnrichOrderRequest request);

    // ── Payments ──────────────────────────────────────────────────────────────

    @UpdateMethod
    ValidatePaymentResponse validatePayment(ValidatePaymentRequest request);

    @UpdateValidatorMethod(updateName = "validatePayment")
    void validateValidatePayment(ValidatePaymentRequest request);

    // ── Inventory ─────────────────────────────────────────────────────────────

    @UpdateMethod
    LookupInventoryAddressResponse lookupInventoryAddress(LookupInventoryAddressRequest request);

    @UpdateValidatorMethod(updateName = "lookupInventoryAddress")
    void validateLookupInventoryAddress(LookupInventoryAddressRequest request);

    @UpdateMethod
    FindAlternateWarehouseResponse findAlternateWarehouse(FindAlternateWarehouseRequest request);

    @UpdateValidatorMethod(updateName = "findAlternateWarehouse")
    void validateFindAlternateWarehouse(FindAlternateWarehouseRequest request);
}
