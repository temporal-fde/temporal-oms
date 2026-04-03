package com.acme.processing.workflows;

import com.acme.proto.acme.processing.domain.processing.v1.*;
import io.temporal.workflow.*;

@WorkflowInterface
public interface SupportTeam {
    @WorkflowMethod
    void execute(InitializeSupportTeam request);

    @UpdateValidatorMethod(updateName = "validateOrder")
    void validateValidateOrder(ManuallyValidateOrderRequest request);

    // TODO should I SIGNAL or UPDATE
    // What are the benefits of one over the other?
    @UpdateMethod
    ManuallyValidateOrderResponse validateOrder(ManuallyValidateOrderRequest request);

    @UpdateMethod
    void completeOrderValidation(String orderId);

    @QueryMethod
    GetSupportTeamStateResponse getState();
}
