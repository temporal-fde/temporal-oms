package com.acme.oms.services;

import com.acme.proto.acme.processing.domain.processing.v1.ValidatePaymentRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidatePaymentResponse;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

@Service
public interface PaymentsService {

    @Operation
    ValidatePaymentResponse validatePayment(ValidatePaymentRequest request);
}
