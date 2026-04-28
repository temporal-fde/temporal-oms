package com.acme.apps.services;

import com.acme.apps.workflows.Integrations;
import com.acme.oms.services.InventoryService;
import com.acme.proto.acme.apps.domain.apps.v1.StartIntegrationsRequest;
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
import io.temporal.api.enums.v1.WorkflowIdConflictPolicy;
import io.temporal.api.enums.v1.WorkflowIdReusePolicy;
import io.temporal.client.UpdateOptions;
import io.temporal.client.WithStartWorkflowOperation;
import io.temporal.client.WorkflowClient;
import io.temporal.client.WorkflowOptions;
import io.temporal.client.WorkflowUpdateStage;
import io.temporal.nexus.Nexus;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component("inventory-service")
@ServiceImpl(service = InventoryService.class)
public class InventoryServiceImpl {

    private static final String WORKFLOW_ID = "integrations";
    private static final String TASK_QUEUE  = "integrations";

    private final Logger logger = LoggerFactory.getLogger(InventoryServiceImpl.class);

    @OperationImpl
    public OperationHandler<LookupInventoryAddressRequest, LookupInventoryAddressResponse> lookupInventoryAddress() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("lookupInventoryAddress Nexus operation, items={}", request.getItemsCount());
            return executeUpdate(stub -> WorkflowClient.executeUpdateWithStart(
                    stub::lookupInventoryAddress, request,
                    UpdateOptions.<LookupInventoryAddressResponse>newBuilder()
                            .setWaitForStage(WorkflowUpdateStage.COMPLETED).build(),
                    new WithStartWorkflowOperation<>(stub::execute, StartIntegrationsRequest.getDefaultInstance())));
        });
    }

    @OperationImpl
    public OperationHandler<FindAlternateWarehouseRequest, FindAlternateWarehouseResponse> findAlternateWarehouse() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("findAlternateWarehouse Nexus operation, currentAddressId={}",
                    request.getCurrentAddressId());
            return executeUpdate(stub -> WorkflowClient.executeUpdateWithStart(
                    stub::findAlternateWarehouse, request,
                    UpdateOptions.<FindAlternateWarehouseResponse>newBuilder()
                            .setWaitForStage(WorkflowUpdateStage.COMPLETED).build(),
                    new WithStartWorkflowOperation<>(stub::execute, StartIntegrationsRequest.getDefaultInstance())));
        });
    }

    @OperationImpl
    public OperationHandler<HoldItemsRequest, HoldItemsResponse> holdItems() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("holdItems Nexus operation, order_id={}", request.getOrderId());
            return executeUpdate(stub -> WorkflowClient.executeUpdateWithStart(
                    stub::holdItems, request,
                    UpdateOptions.<HoldItemsResponse>newBuilder()
                            .setWaitForStage(WorkflowUpdateStage.COMPLETED).build(),
                    new WithStartWorkflowOperation<>(stub::execute, StartIntegrationsRequest.getDefaultInstance())));
        });
    }

    @OperationImpl
    public OperationHandler<ReserveItemsRequest, ReserveItemsResponse> reserveItems() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("reserveItems Nexus operation, order_id={}", request.getOrderId());
            return executeUpdate(stub -> WorkflowClient.executeUpdateWithStart(
                    stub::reserveItems, request,
                    UpdateOptions.<ReserveItemsResponse>newBuilder()
                            .setWaitForStage(WorkflowUpdateStage.COMPLETED).build(),
                    new WithStartWorkflowOperation<>(stub::execute, StartIntegrationsRequest.getDefaultInstance())));
        });
    }

    @OperationImpl
    public OperationHandler<DeductInventoryRequest, DeductInventoryResponse> deductInventory() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("deductInventory Nexus operation, order_id={}", request.getOrderId());
            return executeUpdate(stub -> WorkflowClient.executeUpdateWithStart(
                    stub::deductInventory, request,
                    UpdateOptions.<DeductInventoryResponse>newBuilder()
                            .setWaitForStage(WorkflowUpdateStage.COMPLETED).build(),
                    new WithStartWorkflowOperation<>(stub::execute, StartIntegrationsRequest.getDefaultInstance())));
        });
    }

    @OperationImpl
    public OperationHandler<ReleaseHoldRequest, ReleaseHoldResponse> releaseHold() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("releaseHold Nexus operation, order_id={}", request.getOrderId());
            return executeUpdate(stub -> WorkflowClient.executeUpdateWithStart(
                    stub::releaseHold, request,
                    UpdateOptions.<ReleaseHoldResponse>newBuilder()
                            .setWaitForStage(WorkflowUpdateStage.COMPLETED).build(),
                    new WithStartWorkflowOperation<>(stub::execute, StartIntegrationsRequest.getDefaultInstance())));
        });
    }

    private <T> T executeUpdate(java.util.function.Function<Integrations, T> fn) {
        WorkflowClient client = Nexus.getOperationContext().getWorkflowClient();
        WorkflowOptions wfOptions = WorkflowOptions.newBuilder()
                .setWorkflowId(WORKFLOW_ID)
                .setTaskQueue(TASK_QUEUE)
                .setWorkflowIdConflictPolicy(WorkflowIdConflictPolicy.WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING)
                .setWorkflowIdReusePolicy(WorkflowIdReusePolicy.WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE_FAILED_ONLY)
                .build();
        return fn.apply(client.newWorkflowStub(Integrations.class, wfOptions));
    }
}
