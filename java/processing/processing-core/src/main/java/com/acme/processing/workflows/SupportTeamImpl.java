package com.acme.processing.workflows;


import com.acme.processing.workflows.activities.CommerceApp;
import com.acme.processing.workflows.activities.Support;
import com.acme.proto.acme.processing.domain.processing.v1.*;
import io.temporal.activity.ActivityOptions;
import io.temporal.failure.ApplicationFailure;
import io.temporal.workflow.ContinueAsNewOptions;
import io.temporal.workflow.Workflow;
import io.temporal.workflow.WorkflowInit;

import java.time.Duration;
import java.util.UUID;

public class SupportTeamImpl implements SupportTeam {

    private final Support support;
    private GetSupportTeamStateResponse state;

    @WorkflowInit
    public SupportTeamImpl(InitializeSupportTeam args) {
        this.state = GetSupportTeamStateResponse.newBuilder().addAllValidationRequests(args.getValidationRequestsList()).build();

        this.support = Workflow.newActivityStub(Support.class,
                ActivityOptions.newBuilder()
                        .setScheduleToCloseTimeout(Duration.ofSeconds(60))
                        .build());
    }
    @Override
    public void execute(InitializeSupportTeam request) {
        if(this.state.getValidationRequestsCount() > 500) {
            // we've reached an arbitrary threshhold so do a continue as new to keep it sane
            var can = Workflow.newContinueAsNewStub(SupportTeam.class);
            Workflow.await(Workflow::isEveryHandlerFinished);
            can.execute(InitializeSupportTeam.newBuilder().addAllValidationRequests(this.state.getValidationRequestsList()).build());
            return;
        }
        Workflow.await(()->false);
    }

    @Override
    public void validateValidateOrder(ManuallyValidateOrderRequest request) {
        if(!request.hasOrder()){
            throw new IllegalArgumentException("Order is required");
        }
    }

    @Override
    public ManuallyValidateOrderResponse validateOrder(ManuallyValidateOrderRequest request) {
        this.state = this.state.toBuilder().addValidationRequests(request).build();
        return ManuallyValidateOrderResponse.getDefaultInstance();
    }

    @Override
    public void completeOrderValidation(String orderId) {
        var request = this.state.getValidationRequestsList().stream().filter(r -> r.getOrder().getOrderId().equals(orderId)).findFirst();
        if(request.isEmpty()) {
            throw ApplicationFailure.newFailure("Cannot find validation request for order: " + orderId, "OrderNotFound");
        }

        var cmd = CompleteOrderValidationRequest.newBuilder()
                .setValidationRequest(request.get())
                .setValidationResponse(ValidateOrderResponse.newBuilder()
                        .setOrder(request.get().getOrder())
                        .setManualCorrectionNeeded(true)
                        .setSupportTicketId("support-team-" + request.get().getOrder().getOrderId())).build();
        this.support.completeOrderValidation(cmd);
        this.state = this.state.toBuilder()
                .clearValidationRequests()
                .addAllValidationRequests(this.state.getValidationRequestsList().stream()
                        .filter(r -> !r.getOrder().getOrderId().equals(orderId))
                        .toList())
                .build();
    }
    @Override
    public GetSupportTeamStateResponse getState() {
        return this.state;
    }
}
