package com.acme.processing.workflows.activities;

import com.acme.proto.acme.processing.domain.processing.v1.CompleteOrderValidationRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ManuallyValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ManuallyValidateOrderResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
import io.temporal.activity.Activity;
import org.springframework.stereotype.Component;

@Component("support-activities")
public class SupportImpl implements Support {
    private final com.acme.processing.services.Support support;

    public SupportImpl(com.acme.processing.services.Support support) {
        this.support = support;
    }
    @Override
    public void completeOrderValidation(CompleteOrderValidationRequest cmd) {
        support.completeOrderValidation(cmd);
    }

    @Override
    public ValidateOrderResponse manuallyValidateOrder(ManuallyValidateOrderRequest cmd) {
        var context = Activity.getExecutionContext();

        support.manuallyValidateOrder(
                ManuallyValidateOrderRequest.newBuilder()
                        .setOrder(cmd.getOrder())
                        .setWorkflowId(context.getInfo().getWorkflowId())
                        .setActivityId(context.getInfo().getActivityId())
                        .setCustomerId(cmd.getCustomerId()).build());

        // asynchronous activity completion
        context.doNotCompleteOnReturn();
        return null;
    }
}
