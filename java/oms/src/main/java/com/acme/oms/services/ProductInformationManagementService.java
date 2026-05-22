package com.acme.oms.services;

import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderResponse;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

@Service
public interface ProductInformationManagementService {

    @Operation
    EnrichOrderResponse enrichOrder(EnrichOrderRequest request);
}
