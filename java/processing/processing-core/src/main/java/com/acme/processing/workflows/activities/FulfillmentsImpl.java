package com.acme.processing.workflows.activities;

import com.acme.proto.acme.processing.domain.processing.v1.FulfillOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.FulfillOrderResponse;
import org.springframework.stereotype.Component;

@Component("fulfillment-activities")
public class FulfillmentsImpl implements Fulfillments{
    @Override
    public FulfillOrderResponse fulfillOrder(FulfillOrderRequest cmd) {
        // send message to Kafka for fulfillment
        return FulfillOrderResponse.getDefaultInstance();
    }
}
