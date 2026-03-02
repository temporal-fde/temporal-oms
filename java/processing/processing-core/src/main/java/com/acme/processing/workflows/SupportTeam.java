package com.acme.processing.workflows;

import com.acme.proto.acme.processing.domain.processing.v1.*;
import io.temporal.workflow.*;

@WorkflowInterface
public interface SupportTeam {
    @WorkflowMethod
    void execute(InitializeSupportTeam request);

    @UpdateValidatorMethod(updateName = "validateOrder")
    void validateValidateOrder(ManuallyValidateOrderRequest request);

    @UpdateMethod
    ManuallyValidateOrderResponse validateOrder(ManuallyValidateOrderRequest request);

    @UpdateMethod
    void completeOrderValidation(String orderId);

    @QueryMethod
    GetSupportTeamStateResponse getState();
}
