package com.acme.apps.services;

import com.acme.apps.workflows.Integrations;
import com.acme.oms.services.CommerceAppService;
import com.acme.proto.acme.apps.domain.apps.v1.StartIntegrationsRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
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

@Component("commerce-app-service")
@ServiceImpl(service = CommerceAppService.class)
public class CommerceAppServiceImpl {

    private static final String WORKFLOW_ID = "integrations";
    private static final String TASK_QUEUE  = "apps";

    private final Logger logger = LoggerFactory.getLogger(CommerceAppServiceImpl.class);

    @OperationImpl
    public OperationHandler<ValidateOrderRequest, ValidateOrderResponse> validateOrder() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("validateOrder Nexus operation, orderId={}", request.getOrder().getOrderId());

            WorkflowClient client = Nexus.getOperationContext().getWorkflowClient();
            WorkflowOptions wfOptions = WorkflowOptions.newBuilder()
                    .setWorkflowId(WORKFLOW_ID)
                    .setTaskQueue(TASK_QUEUE)
                    .setWorkflowIdConflictPolicy(
                            WorkflowIdConflictPolicy.WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING)
                    .setWorkflowIdReusePolicy(
                            WorkflowIdReusePolicy.WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE_FAILED_ONLY)
                    .build();

            Integrations stub = client.newWorkflowStub(Integrations.class, wfOptions);

            return WorkflowClient.executeUpdateWithStart(
                    stub::validateOrder,
                    request,
                    UpdateOptions.<ValidateOrderResponse>newBuilder()
                            .setWaitForStage(WorkflowUpdateStage.COMPLETED)
                            .build(),
                    new WithStartWorkflowOperation<>(
                            stub::execute,
                            StartIntegrationsRequest.getDefaultInstance()));
        });
    }
}
