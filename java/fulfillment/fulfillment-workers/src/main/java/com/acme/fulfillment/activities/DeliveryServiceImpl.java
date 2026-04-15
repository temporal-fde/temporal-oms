package com.acme.fulfillment.activities;

import com.acme.fulfillment.workflows.activities.DeliveryService;
import com.acme.proto.acme.common.v1.Money;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * Stub implementation — returns a single carrier rate with a placeholder shipment ID.
 * Phase 6: replace with real EasyPost Shipment creation + carrier rate query.
 */
@Component("deliveryServiceActivities")
public class DeliveryServiceImpl implements DeliveryService {

    private static final Logger logger = LoggerFactory.getLogger(DeliveryServiceImpl.class);

    @Override
    public GetCarrierRatesResponse getCarrierRates(GetCarrierRatesRequest request) {
        logger.info("getCarrierRates stub: order_id={}, easypost_address_id={}",
                request.getOrderId(), request.getEasypostAddressId());

        var stubRate = CarrierRate.newBuilder()
                .setRateId("rate_stub_" + request.getOrderId())
                .setCarrier("UPS")
                .setServiceLevel("Ground")
                .setCost(Money.newBuilder().setCurrency("USD").setUnits(999L).build()) // $9.99
                .setEstimatedDays(5)
                .build();

        return GetCarrierRatesResponse.newBuilder()
                .setShipmentId("shipment_stub_" + request.getOrderId())
                .addRates(stubRate)
                .build();
    }
}
