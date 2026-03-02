package com.acme.apps.workflows.activities;

import com.acme.proto.acme.apps.domain.apps.v1.CompleteOrderRequestExecutionOptions;
import com.acme.proto.acme.apps.domain.apps.v1.GetOptionsRequest;
import com.acme.proto.acme.oms.v1.OmsProperties;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

@ActivityInterface
public interface Options {
    @ActivityMethod
    CompleteOrderRequestExecutionOptions getOptions(GetOptionsRequest cmd);
}
