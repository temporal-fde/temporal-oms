package com.acme.processing.services;

import com.acme.processing.workflows.SupportTeam;
import com.acme.proto.acme.processing.domain.processing.v1.*;
import io.temporal.api.enums.v1.WorkflowIdConflictPolicy;
import io.temporal.client.*;
import org.springframework.stereotype.Component;

@Component("support")
public class SupportImpl implements Support{
    private WorkflowClient workflowClient;

    public SupportImpl(WorkflowClient workflowClient) {
        this.workflowClient = workflowClient;
    }

    @Override
    public void manuallyValidateOrder(ManuallyValidateOrderRequest request) {
        var wf = workflowClient.newWorkflowStub(SupportTeam.class,
                WorkflowOptions.newBuilder()
                        .setWorkflowId("support-team")
                        .setTaskQueue("support")
                        .setWorkflowIdConflictPolicy(WorkflowIdConflictPolicy.WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING)
                        .build());
        WorkflowClient.executeUpdateWithStart(
                wf::validateOrder,
                request,
                UpdateOptions.<ManuallyValidateOrderRequest>newBuilder().setWaitForStage(WorkflowUpdateStage.COMPLETED).build(),
                new WithStartWorkflowOperation<>(
                        wf::execute,
                        InitializeSupportTeam.getDefaultInstance()
                )
        );
    }

    @Override
    public void completeOrderValidation(CompleteOrderValidationRequest request) {

        var act = workflowClient.newActivityCompletionClient();
        var original = request.getValidationRequest();
        act.complete(original.getWorkflowId(), java.util.Optional.empty(),
                original.getActivityId(),
                request.getValidationResponse());
    }
}
