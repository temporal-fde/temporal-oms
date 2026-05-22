package com.acme.oms.services;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.DeductInventoryRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.DeductInventoryResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.HoldItemsRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.HoldItemsResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReleaseHoldRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReleaseHoldResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReserveItemsRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReserveItemsResponse;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

@Service
public interface InventoryService {

    @Operation
    LookupInventoryAddressResponse lookupInventoryAddress(LookupInventoryAddressRequest request);

    @Operation
    FindAlternateWarehouseResponse findAlternateWarehouse(FindAlternateWarehouseRequest request);

    @Operation
    HoldItemsResponse holdItems(HoldItemsRequest request);

    @Operation
    ReserveItemsResponse reserveItems(ReserveItemsRequest request);

    @Operation
    DeductInventoryResponse deductInventory(DeductInventoryRequest request);

    @Operation
    ReleaseHoldResponse releaseHold(ReleaseHoldRequest request);
}
