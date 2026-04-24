package com.acme.processing.workflows.activities;

import com.acme.proto.acme.processing.domain.processing.v1.ProcessOrderRequestExecutionOptions;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

@ActivityInterface
public interface Options {
    @ActivityMethod
    ProcessOrderRequestExecutionOptions getOptions(ProcessOrderRequestExecutionOptions input);
}
