package com.acme.fulfillment.activities;

import com.acme.fulfillment.workflows.activities.Carriers;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * Stub implementation — returns a placeholder tracking number and label URL.
 * Phase 6: replace with real EasyPost label creation using selected rate_id.
 */
@Component("carriersActivities")
public class CarriersImpl implements Carriers {

    private static final Logger logger = LoggerFactory.getLogger(CarriersImpl.class);

    @Override
    public PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request) {
        logger.info("printShippingLabel stub: order_id={}, shipment_id={}, rate_id={}",
                request.getOrderId(), request.getShipmentId(), request.getRateId());

        return PrintShippingLabelResponse.newBuilder()
                .setTrackingNumber("1Z999AA1" + request.getOrderId().replace("-", "").substring(0, 8).toUpperCase())
                .setLabelUrl("https://easypost.com/labels/stub_" + request.getShipmentId() + ".pdf")
                .build();
    }
}
