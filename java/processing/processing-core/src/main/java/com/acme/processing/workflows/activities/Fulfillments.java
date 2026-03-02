package com.acme.processing.workflows.activities;

import com.acme.proto.acme.processing.domain.processing.v1.FulfillOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.FulfillOrderResponse;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

@ActivityInterface
public interface Fulfillments {
    @ActivityMethod
    FulfillOrderResponse fulfillOrder(FulfillOrderRequest cmd);
}
