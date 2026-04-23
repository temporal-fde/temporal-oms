package com.acme.oms.services;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressResponse;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

@Service
public interface InventoryService {

    @Operation
    LookupInventoryAddressResponse lookupInventoryAddress(LookupInventoryAddressRequest request);

    @Operation
    FindAlternateWarehouseResponse findAlternateWarehouse(FindAlternateWarehouseRequest request);
}
