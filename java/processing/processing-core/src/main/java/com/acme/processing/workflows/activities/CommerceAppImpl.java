package com.acme.processing.workflows.activities;

import com.acme.processing.services.Support;
import com.acme.proto.acme.processing.domain.processing.v1.*;
import io.temporal.activity.Activity;
import org.springframework.stereotype.Component;

@Component("commerce-app-activities")
public class CommerceAppImpl implements CommerceApp{


    @Override
    public ValidateOrderResponse validateOrder(ValidateOrderRequest cmd) {

        var isInvalid = cmd.getOrder().getOrderId().contains("invalid");
        // TODO call commerce-app API to validate order

        return ValidateOrderResponse.newBuilder()
                .setOrder(cmd.getOrder())
                        .setManualCorrectionNeeded(isInvalid)
                                .build();
    }


}
