package com.acme.enablements.services;

import com.acme.enablements.integrations.EnablementsIntegrationsClient;
import com.acme.oms.services.InventoryService;
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
import io.nexusrpc.handler.OperationHandler;
import io.nexusrpc.handler.OperationImpl;
import io.nexusrpc.handler.ServiceImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

@Component("inventory-service")
@ServiceImpl(service = InventoryService.class)
public class InventoryServiceImpl {

    private final Logger logger = LoggerFactory.getLogger(InventoryServiceImpl.class);
    private final EnablementsIntegrationsClient enablements;

    public InventoryServiceImpl(EnablementsIntegrationsClient enablements) {
        this.enablements = enablements;
    }

    @OperationImpl
    public OperationHandler<LookupInventoryAddressRequest, LookupInventoryAddressResponse> lookupInventoryAddress() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("lookupInventoryAddress Nexus adapter via enablements-api, items={}", request.getItemsCount());
            return enablements.lookupInventoryAddress(request);
        });
    }

    @OperationImpl
    public OperationHandler<FindAlternateWarehouseRequest, FindAlternateWarehouseResponse> findAlternateWarehouse() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("findAlternateWarehouse Nexus adapter via enablements-api, currentAddressId={}",
                    request.getCurrentAddressId());
            return enablements.findAlternateWarehouse(request);
        });
    }

    @OperationImpl
    public OperationHandler<HoldItemsRequest, HoldItemsResponse> holdItems() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("holdItems Nexus adapter via enablements-api, order_id={}", request.getOrderId());
            return enablements.holdItems(request);
        });
    }

    @OperationImpl
    public OperationHandler<ReserveItemsRequest, ReserveItemsResponse> reserveItems() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("reserveItems Nexus adapter via enablements-api, order_id={}", request.getOrderId());
            return enablements.reserveItems(request);
        });
    }

    @OperationImpl
    public OperationHandler<DeductInventoryRequest, DeductInventoryResponse> deductInventory() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("deductInventory Nexus adapter via enablements-api, order_id={}", request.getOrderId());
            return enablements.deductInventory(request);
        });
    }

    @OperationImpl
    public OperationHandler<ReleaseHoldRequest, ReleaseHoldResponse> releaseHold() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("releaseHold Nexus adapter via enablements-api, order_id={}", request.getOrderId());
            return enablements.releaseHold(request);
        });
    }
}
