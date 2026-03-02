package com.acme.oms.services;

import com.acme.proto.acme.processing.domain.processing.v1.GetProcessOrderStateResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ProcessOrderRequest;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

@Service
public interface Processing {
    @Operation
    GetProcessOrderStateResponse processOrder(ProcessOrderRequest cmd);
}
