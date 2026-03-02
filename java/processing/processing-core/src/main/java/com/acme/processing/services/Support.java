package com.acme.processing.services;


import com.acme.proto.acme.processing.domain.processing.v1.CompleteOrderValidationRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ManuallyValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ManuallyValidateOrderResponse;

public interface Support {
    void manuallyValidateOrder(ManuallyValidateOrderRequest request);
    void completeOrderValidation(CompleteOrderValidationRequest request);
}
