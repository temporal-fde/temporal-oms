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
import io.temporal.common.VersioningBehavior;
import io.temporal.workflow.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class IntegrationsImpl implements Integrations {

    private static final Logger logger = LoggerFactory.getLogger(IntegrationsImpl.class);

    @WorkflowInit
    public IntegrationsImpl(StartIntegrationsRequest request) {}

    @Override
    @WorkflowVersioningBehavior(VersioningBehavior.PINNED)
    public void execute(StartIntegrationsRequest request) {
        logger.info("apps.Integrations started (singleton)");
        Workflow.await(() -> false);
    }

    // ── CommerceApp ───────────────────────────────────────────────────────────

    @Override
    public void validateValidateOrder(ValidateOrderRequest request) {}

    @Override
    public ValidateOrderResponse validateOrder(ValidateOrderRequest request) {
        boolean invalid = request.getOrder().getOrderId().contains("invalid");
        logger.info("validateOrder orderId={}, invalid={}", request.getOrder().getOrderId(), invalid);
        return ValidateOrderResponse.newBuilder()
                .setOrder(request.getOrder())
                .setManualCorrectionNeeded(invalid)
                .build();
    }

    // ── PIMS ──────────────────────────────────────────────────────────────────

    @Override
    public void validateEnrichOrder(EnrichOrderRequest request) {}

    @Override
    public EnrichOrderResponse enrichOrder(EnrichOrderRequest request) {
        logger.info("enrichOrder orderId={}", request.getOrder().getOrderId());
        return EnrichOrderResponse.getDefaultInstance();
    }

    // ── Payments ──────────────────────────────────────────────────────────────

    @Override
    public void validateValidatePayment(ValidatePaymentRequest request) {}

    @Override
    public ValidatePaymentResponse validatePayment(ValidatePaymentRequest request) {
        logger.info("validatePayment rrn={}", request.getRrn());
        return ValidatePaymentResponse.newBuilder()
                .setValid(true)
                .setPaymentStatus("AUTHORIZED")
                .setActualAmountCents(request.getExpectedAmountCents())
                .build();
    }

    // ── Inventory ─────────────────────────────────────────────────────────────

    @Override
    public void validateLookupInventoryAddress(LookupInventoryAddressRequest request) {}

    @Override
    public LookupInventoryAddressResponse lookupInventoryAddress(LookupInventoryAddressRequest request) {
        logger.info("lookupInventoryAddress items={}", request.getItemsCount());
        return LookupInventoryAddressResponse.getDefaultInstance();
    }

    @Override
    public void validateFindAlternateWarehouse(FindAlternateWarehouseRequest request) {}

    @Override
    public FindAlternateWarehouseResponse findAlternateWarehouse(FindAlternateWarehouseRequest request) {
        logger.info("findAlternateWarehouse currentAddressId={}", request.getCurrentAddressId());
        return FindAlternateWarehouseResponse.getDefaultInstance();
    }
}
