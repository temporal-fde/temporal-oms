package com.acme.processing.services;

import com.acme.oms.services.Processing;
import com.acme.processing.workflows.Order;
import com.acme.proto.acme.processing.domain.processing.v1.GetProcessOrderStateResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ProcessOrderRequest;
import io.nexusrpc.handler.*;
import io.temporal.api.enums.v1.WorkflowIdConflictPolicy;
import io.temporal.api.enums.v1.WorkflowIdReusePolicy;
import io.temporal.client.*;
import io.temporal.nexus.Nexus;
import io.temporal.nexus.NexusOperationContext;
import io.temporal.nexus.WorkflowHandle;
import io.temporal.nexus.WorkflowRunOperation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component("processing-service")
@ServiceImpl(service = Processing.class)
public class ProcessingImpl {
    private Logger logger = LoggerFactory.getLogger(ProcessingImpl.class);
    // sync operation
    private OperationHandler<ProcessOrderRequest, GetProcessOrderStateResponse> processOrderSync() {
        // This implementation uses a synchronous operation here with an UpdateWithStart call on the inside.
        // The `processOrder` Update operation must therefore remain under 10s per Nexus limits on sync requests.
        // Ideally, this would be an async Operation but Nexus does not support UpdateWithStart for async ops.

        return OperationHandler.sync((ctx, details, request)-> {
            var wfOpts = WorkflowOptions.newBuilder()
                    .setWorkflowId(request.getOrderId())
                    .setWorkflowIdReusePolicy(WorkflowIdReusePolicy.WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE_FAILED_ONLY)
                    .build();
            var tcli = Nexus.getOperationContext().getWorkflowClient();
            var workflow = tcli.newWorkflowStub(Order.class, wfOpts);
            return workflow.execute(request);
            // we block on the update to complete here
            // validations in the update, etc must be speedy to fit within the 10sec limit
//            return WorkflowClient.executeUpdateWithStart(
//                    workflow::processOrder,
//                    request,
//                    UpdateOptions.<GetProcessOrderStateResponse>newBuilder().setWaitForStage(WorkflowUpdateStage.ACCEPTED).build(),
//                    new WithStartWorkflowOperation<>(workflow::execute, request));
        });

    }

    // async operation
    private OperationHandler<ProcessOrderRequest, GetProcessOrderStateResponse> processOrderAsync() {
        return WorkflowRunOperation.fromWorkflowMethod((ctx, details, request) -> {

            var wfOpts = WorkflowOptions.newBuilder()
                    .setWorkflowId(request.getOrderId())
                    .setTaskQueue("processing")
                    .setWorkflowIdConflictPolicy(WorkflowIdConflictPolicy.WORKFLOW_ID_CONFLICT_POLICY_FAIL)
                    // using ALLOW_DUPLICATE so we won't fail the operation if the workflow completes
                    // as it would if we used ALLOW_DUPLICATE_FAILED_ONLY
                    .setWorkflowIdReusePolicy(WorkflowIdReusePolicy.WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE)
                    .build();
            var tcli = Nexus.getOperationContext().getWorkflowClient();
            var workflow = tcli.newWorkflowStub(Order.class, wfOpts);
            return workflow::execute;
//            // we block on the update to complete,
//            // but validations, etc can take as long as they want
//            var ups = WorkflowClient.executeUpdateWithStart(
//                    workflow::processOrder,
//                    request,
//                    UpdateOptions.<GetProcessOrderStateResponse>newBuilder().setWaitForStage(WorkflowUpdateStage.COMPLETED).build(),
//                    new WithStartWorkflowOperation<>(workflow::execute, request));
//            // but the operation is blocked until the whole workflow is complete
//            return workflow::execute;
        });
    }
    @OperationImpl
    public OperationHandler<ProcessOrderRequest, GetProcessOrderStateResponse> processOrder() {
        return processOrderAsync();
    }
}
