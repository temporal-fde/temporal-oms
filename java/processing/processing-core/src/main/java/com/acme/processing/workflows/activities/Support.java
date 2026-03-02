package com.acme.processing.workflows.activities;

import com.acme.proto.acme.processing.domain.processing.v1.CompleteOrderValidationRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ManuallyValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

@ActivityInterface
public interface Support {
    @ActivityMethod
    void completeOrderValidation(CompleteOrderValidationRequest cmd);

    @ActivityMethod
    ValidateOrderResponse manuallyValidateOrder(ManuallyValidateOrderRequest cmd);
}
