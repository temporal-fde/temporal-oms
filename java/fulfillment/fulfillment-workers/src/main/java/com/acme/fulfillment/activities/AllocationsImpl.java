package com.acme.fulfillment.activities;

import com.acme.fulfillment.workflows.activities.Allocations;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * Stub implementation — returns defaults for all allocation operations.
 * Phase 6: replace with real inventory service integration.
 */
@Component("allocationsActivities")
public class AllocationsImpl implements Allocations {

    private static final Logger logger = LoggerFactory.getLogger(AllocationsImpl.class);

    @Override
    public HoldItemsResponse holdItems(HoldItemsRequest request) {
        logger.info("holdItems stub: order_id={}, items={}", request.getOrderId(), request.getItemsCount());
        return HoldItemsResponse.newBuilder()
                .setHoldId("hold_stub_" + request.getOrderId())
                .build();
    }

    @Override
    public ReserveItemsResponse reserveItems(ReserveItemsRequest request) {
        logger.info("reserveItems stub: order_id={}", request.getOrderId());
        return ReserveItemsResponse.newBuilder()
                .setReservationId("reservation_stub_" + request.getOrderId())
                .build();
    }

    @Override
    public DeductInventoryResponse deductInventory(DeductInventoryRequest request) {
        logger.info("deductInventory stub: order_id={}", request.getOrderId());
        return DeductInventoryResponse.newBuilder()
                .setSuccess(true)
                .build();
    }

    @Override
    public ReleaseHoldResponse releaseHold(ReleaseHoldRequest request) {
        logger.info("releaseHold stub: order_id={}, hold_id={}", request.getOrderId(), request.getHoldId());
        return ReleaseHoldResponse.newBuilder()
                .setSuccess(true)
                .build();
    }
}
