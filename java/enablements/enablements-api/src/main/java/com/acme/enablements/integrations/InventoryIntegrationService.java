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
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class InventoryIntegrationService {

    private static final Logger logger = LoggerFactory.getLogger(InventoryIntegrationService.class);

    private final ShippingFixtureService shipping;

    public InventoryIntegrationService(ShippingFixtureService shipping) {
        this.shipping = shipping;
    }

    public LookupInventoryAddressResponse lookupInventoryAddress(LookupInventoryAddressRequest request) {
        logger.info("lookupInventoryAddress items={}, addressId={}",
                request.getItemsCount(), request.hasAddressId() ? request.getAddressId() : "");

        if (request.hasAddressId() && !request.getAddressId().isBlank()) {
            return shipping.addressById(request.getAddressId())
                    .map(address -> LookupInventoryAddressResponse.newBuilder().setAddress(address).build())
                    .orElseGet(LookupInventoryAddressResponse::getDefaultInstance);
        }

        String skuId = request.getItemsCount() > 0 ? request.getItems(0).getSkuId() : "";
        var warehouse = shipping.warehouses().stream()
                .filter(wh -> handlesSku(wh, skuId))
                .findFirst()
                .orElseGet(() -> shipping.warehouses().getFirst());

        return shipping.addressById(warehouse.addressId())
                .map(address -> LookupInventoryAddressResponse.newBuilder().setAddress(address).build())
                .orElseGet(LookupInventoryAddressResponse::getDefaultInstance);
    }

    public FindAlternateWarehouseResponse findAlternateWarehouse(FindAlternateWarehouseRequest request) {
        logger.info("findAlternateWarehouse currentAddressId={}", request.getCurrentAddressId());
        String skuId = request.getItemsCount() > 0 ? request.getItems(0).getSkuId() : "";

        Optional<ShippingFixture.WarehouseFixture> alternate = shipping.warehouses().stream()
                .filter(wh -> !wh.addressId().equals(request.getCurrentAddressId()))
                .filter(wh -> handlesSku(wh, skuId))
                .findFirst();

        FindAlternateWarehouseResponse.Builder response = FindAlternateWarehouseResponse.newBuilder();
        alternate.flatMap(wh -> shipping.addressById(wh.addressId()))
                .ifPresent(response::setAddress);
        return response.build();
    }

    public HoldItemsResponse holdItems(HoldItemsRequest request) {
        logger.info("holdItems stub: order_id={}, items={}", request.getOrderId(), request.getItemsCount());
        return HoldItemsResponse.newBuilder()
                .setHoldId("hold_stub_" + request.getOrderId())
                .build();
    }

    public ReserveItemsResponse reserveItems(ReserveItemsRequest request) {
        logger.info("reserveItems stub: order_id={}", request.getOrderId());
        return ReserveItemsResponse.newBuilder()
                .setReservationId("reservation_stub_" + request.getOrderId())
                .build();
    }

    public DeductInventoryResponse deductInventory(DeductInventoryRequest request) {
        logger.info("deductInventory stub: order_id={}", request.getOrderId());
        return DeductInventoryResponse.newBuilder()
                .setSuccess(true)
                .build();
    }

    public ReleaseHoldResponse releaseHold(ReleaseHoldRequest request) {
        logger.info("releaseHold stub: order_id={}, hold_id={}", request.getOrderId(), request.getHoldId());
        return ReleaseHoldResponse.newBuilder()
                .setSuccess(true)
                .build();
    }

    private static boolean handlesSku(ShippingFixture.WarehouseFixture warehouse, String skuId) {
        if (warehouse.skuPrefixes().isEmpty()) {
            return true;
        }
        return warehouse.skuPrefixes().stream().anyMatch(skuId::startsWith);
    }
}
