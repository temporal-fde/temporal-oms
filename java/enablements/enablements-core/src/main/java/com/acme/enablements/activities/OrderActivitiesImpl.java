package com.acme.enablements.activities;

import com.acme.proto.acme.enablements.v1.SubmitOrdersRequest;
import com.acme.proto.acme.enablements.v1.SubmitOrdersResponse;
import io.temporal.activity.Activity;
import io.temporal.client.ActivityCompletionException;
import io.temporal.failure.CanceledFailure;
import io.temporal.workflow.Workflow;

import java.time.Duration;

public class OrderActivitiesImpl implements OrderActivities {
    @Override
    public SubmitOrdersResponse submitOrders(SubmitOrdersRequest cmd) {
        var res = SubmitOrdersResponse.getDefaultInstance();
        var ctx = Activity.getExecutionContext();
        var sleepIntervalMs = (60 / cmd.getSubmitRatePerMin()) * 1000;
        var canceled = false;
        while(!canceled) {
            try {
                ctx.heartbeat(null);
                // call /orders/{order_id} submit order
                res = res.toBuilder().setOrdersSubmittedCount(res.getOrdersSubmittedCount() + 1).build();
                try {
                    Thread.sleep(Duration.ofMillis(sleepIntervalMs));
                } catch (InterruptedException e) {
                    canceled = true;
                }
            } catch (ActivityCompletionException e){
                canceled = true;
            }
        }
        return res;
    }
}
