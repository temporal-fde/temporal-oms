package com.acme.enablements.integrations;

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
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;

public interface EnablementsIntegrationsClient {

    ValidateOrderResponse validateOrder(ValidateOrderRequest request);

    EnrichOrderResponse enrichOrder(EnrichOrderRequest request);

    LookupInventoryAddressResponse lookupInventoryAddress(LookupInventoryAddressRequest request);

    FindAlternateWarehouseResponse findAlternateWarehouse(FindAlternateWarehouseRequest request);

    HoldItemsResponse holdItems(HoldItemsRequest request);

    ReserveItemsResponse reserveItems(ReserveItemsRequest request);

    DeductInventoryResponse deductInventory(DeductInventoryRequest request);

    ReleaseHoldResponse releaseHold(ReleaseHoldRequest request);
}
