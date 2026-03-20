package com.acme.enablements.workflows;

import com.acme.enablements.activities.DeploymentActivities;
import com.acme.enablements.activities.OrderActivities;
import com.acme.proto.acme.enablements.v1.StartWorkerVersionEnablementRequest;
import com.acme.proto.acme.enablements.v1.SubmitOrdersRequest;
import com.acme.proto.acme.enablements.v1.WorkerVersionEnablementState;
import io.temporal.activity.ActivityOptions;
import io.temporal.common.RetryOptions;
import io.temporal.workflow.Workflow;
import io.temporal.workflow.WorkflowInit;
import org.slf4j.Logger;

import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Implementation of WorkerVersionEnablementWorkflow for demonstrating safe version transitions.
 * <p>
 * This workflow continuously submits orders to the OMS at a configured rate,
 * allowing manual control over worker version transitions via signals.
 */
public class WorkerVersionEnablementWorkflowImpl implements WorkerVersionEnablementWorkflow {

    private static final Logger logger = Workflow.getLogger(WorkerVersionEnablementWorkflowImpl.class);

    private final OrderActivities orderActivities =
            Workflow.newActivityStub(
                    OrderActivities.class,
                    ActivityOptions.newBuilder()
                            .setStartToCloseTimeout(Duration.ofSeconds(30))
                            .setRetryOptions(
                                    RetryOptions.newBuilder()
                                            .setInitialInterval(Duration.ofSeconds(1))
                                            .setMaximumInterval(Duration.ofSeconds(10))
                                            .setBackoffCoefficient(2.0)
                                            .setMaximumAttempts(5)
                                            .build())
                            .build());

    private final DeploymentActivities deploymentActivities =
            Workflow.newActivityStub(
                    DeploymentActivities.class,
                    ActivityOptions.newBuilder()
                            .setStartToCloseTimeout(Duration.ofMinutes(5))
                            .setRetryOptions(
                                    RetryOptions.newBuilder()
                                            .setInitialInterval(Duration.ofSeconds(5))
                                            .setMaximumInterval(Duration.ofSeconds(30))
                                            .setBackoffCoefficient(2.0)
                                            .setMaximumAttempts(3)
                                            .build())
                            .build());
    private final WorkerVersionEnablementState state;

    private StartWorkerVersionEnablementRequest request;
    private WorkerVersionEnablementState.DemoPhase currentPhase =
            WorkerVersionEnablementState.DemoPhase.RUNNING_V1_ONLY;
    private Instant lastTransitionAt = null;
    private final AtomicInteger ordersSubmittedCount = new AtomicInteger(0);
    private final AtomicBoolean isPaused = new AtomicBoolean(false);
    private final AtomicBoolean transitionSignalReceived = new AtomicBoolean(false);

    @WorkflowInit
    public WorkerVersionEnablementWorkflowImpl(StartWorkerVersionEnablementRequest request) {
        this.state = WorkerVersionEnablementState.newBuilder().setArgs(request).build();
    }


    @Override
    public void startDemonstration(StartWorkerVersionEnablementRequest req) {
        var submitScope = Workflow.newCancellationScope(() -> {
            submitOrdersUntilSignal();
        })
        this.request = req;
        logger.info(
                "Starting enablement demonstration: {} with {} orders at {}/min",
                req.getDemonstrationId(),
                req.getOrderCount(),
                req.getSubmitRatePerMin());

        // Calculate timing
        long submissionIntervalMs = 60_000L / req.getSubmitRatePerMin();
        long timeoutMs = req.getTimeout().getSeconds() * 1000 + req.getTimeout().getNanos() / 1_000_000L;


        // Phase 1: Submit orders with v1 only
        submitOrdersUntilSignal(req.getOrderCount(), submissionIntervalMs, timeoutMs);

        // Phase 2: If transition signal received, deploy v2 and continue
        if (transitionSignalReceived.get()) {
            currentPhase = WorkerVersionEnablementState.DemoPhase.TRANSITIONING_TO_V2;
            lastTransitionAt = Instant.now();

            // Deploy v2 and register compatibility
            deploymentActivities.deployV2Workers();
            deploymentActivities.registerCompatibility();

            currentPhase = WorkerVersionEnablementState.DemoPhase.RUNNING_BOTH;
            logger.info("V2 workers deployed and compatibility registered");

            // Continue submitting remaining orders (if any)
            long remainingTime =
                    timeoutMs - (Workflow.currentTimeMillis() - System.currentTimeMillis());
            if (remainingTime > 0 && ordersSubmittedCount.get() < req.getOrderCount()) {
                submitRemainingOrders(
                        req.getOrderCount() - ordersSubmittedCount.get(),
                        submissionIntervalMs,
                        remainingTime);
            }
        }

        currentPhase = WorkerVersionEnablementState.DemoPhase.COMPLETE;
        logger.info("Enablement demonstration complete. Total orders submitted: {}",
                ordersSubmittedCount.get());
    }

    @Override
    public WorkerVersionEnablementState getState() {
        if (request == null) {
            // Not yet initialized
            return WorkerVersionEnablementState.getDefaultInstance();
        }

        WorkerVersionEnablementState.Builder stateBuilder =
                WorkerVersionEnablementState.newBuilder()
                        .setDemonstrationId(request.getDemonstrationId())
                        .setCurrentPhase(currentPhase)
                        .setOrdersSubmittedCount(ordersSubmittedCount.get())
                        .setOrdersPerMinute(request.getSubmitRatePerMin());

        if (lastTransitionAt != null) {
            stateBuilder.setLastTransitionAt(
                    com.google.protobuf.Timestamp.newBuilder()
                            .setSeconds(lastTransitionAt.getEpochSecond())
                            .setNanos(lastTransitionAt.getNano())
                            .build());
        }

        // Set active versions based on phase
        if (currentPhase == WorkerVersionEnablementState.DemoPhase.RUNNING_V1_ONLY) {
            stateBuilder.addActiveVersions("v1");
        } else if (currentPhase == WorkerVersionEnablementState.DemoPhase.RUNNING_BOTH ||
                currentPhase == WorkerVersionEnablementState.DemoPhase.TRANSITIONING_TO_V2) {
            stateBuilder.addActiveVersions("v1").addActiveVersions("v2");
        }

        return stateBuilder.build();
    }

    @Override
    public void pause() {
        isPaused.set(true);
        logger.info("Enablement workflow paused");
    }

    @Override
    public void resume() {
        isPaused.set(false);
        logger.info("Enablement workflow resumed");
    }

    @Override
    public void transitionToV2() {
        transitionSignalReceived.set(true);
        logger.info("Received signal to transition to v2");
    }

    private void submitOrdersUntilSignal() {
        // call activity with forever-order-starter
        orderActivities.submitOrders(SubmitOrdersRequest.newBuilder().
                setSubmitRatePerMin(request.getSubmitRatePerMin()).
                setEnablementId(state.getEnablementId()).build());


        logger.info(
                "Completed v1-only phase: submitted {} orders",
                ordersSubmittedCount.get());
    }

    private void submitRemainingOrders(int remaining, long submissionIntervalMs, long remainingTimeMs) {
        long startTime = Workflow.currentTimeMillis();
        int submitted = 0;

        while (submitted < remaining) {
            long elapsedMs = Workflow.currentTimeMillis() - startTime;
            if (elapsedMs >= remainingTimeMs) {
                logger.info("Timeout reached during v2 phase");
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
                submitted++;
                logger.debug("Submitted order (v2 available): {}", orderId);
            } catch (Exception e) {
                logger.warn("Failed to submit order during v2 phase (will continue)", e);
            }

            // Wait for next submission slot
            Workflow.sleep(Duration.ofMillis(submissionIntervalMs));
        }

        logger.info("Completed v2 phase: submitted {} additional orders", submitted);
    }
}
