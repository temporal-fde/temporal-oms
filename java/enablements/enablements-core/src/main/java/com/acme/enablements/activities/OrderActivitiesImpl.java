package com.acme.enablements.activities;

import com.acme.proto.acme.enablements.v1.SubmitOrdersRequest;
import com.acme.proto.acme.enablements.v1.SubmitOrdersResponse;
import io.temporal.workflow.Workflow;

import java.time.Duration;

public class OrderActivitiesImpl implements OrderActivities {
    @Override
    public SubmitOrdersResponse submitOrders(SubmitOrdersRequest cmd) {
        long startTime = Workflow.currentTimeMillis();
        long submissionCount = 0;

        while (ordersSubmittedCount.get() < totalOrders && !transitionSignalReceived.get()) {
            long elapsedMs = Workflow.currentTimeMillis() - startTime;
            if (elapsedMs >= timeoutMs) {
                logger.info("Timeout reached during v1 phase");
                break;
            }

            // Wait if paused
            if (isPaused.get()) {
                Workflow.sleep(Duration.ofSeconds(1));
                continue;
            }

            // Submit order
            try {
                String orderId = orderActivities.submitOrders();
                ordersSubmittedCount.incrementAndGet();
                logger.debug("Submitted order: {}", orderId);
            } catch (Exception e) {
                logger.warn("Failed to submit order (will continue)", e);
            }

            // Wait for next submission slot
            Workflow.sleep(Duration.ofMillis(submissionIntervalMs));
            submissionCount++;
        }
    }
}
