package com.acme.oms.services;

import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

@Service
public interface CommerceAppService {

    @Operation
    ValidateOrderResponse validateOrder(ValidateOrderRequest request);
}
