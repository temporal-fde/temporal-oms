package com.acme.processing.workflows.activities;

import com.acme.proto.acme.processing.domain.processing.v1.*;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

@ActivityInterface
public interface CommerceApp {
    @ActivityMethod
    ValidateOrderResponse validateOrder(ValidateOrderRequest cmd);


}
