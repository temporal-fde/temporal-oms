package com.acme.enablements.workflows;

import com.acme.enablements.activities.DeploymentActivities;
import com.acme.enablements.activities.OrderActivities;
import com.acme.proto.acme.enablements.v1.DeployWorkerVersionRequest;
import com.acme.proto.acme.enablements.v1.StartWorkerVersionEnablementRequest;
import com.acme.proto.acme.enablements.v1.SubmitOrdersRequest;
import com.acme.proto.acme.enablements.v1.WorkerVersionEnablementState;
import io.temporal.activity.ActivityOptions;
import io.temporal.common.RetryOptions;
import io.temporal.workflow.Async;
import io.temporal.workflow.Workflow;
import io.temporal.workflow.WorkflowInit;
import org.slf4j.Logger;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Implementation of WorkerVersionEnablementWorkflow for demonstrating safe version transitions.
 * <p>
 * This workflow continuously submits orders to the OMS at a configured rate,
 * allowing manual control over worker version transitions via signals.
 */
public class WorkerVersionEnablementImpl implements WorkerVersionEnablement {

    private static final Logger logger = Workflow.getLogger(WorkerVersionEnablementImpl.class);

    private final OrderActivities orderActivities =
            Workflow.newActivityStub(
                    OrderActivities.class,
                    ActivityOptions.newBuilder()
                            .setStartToCloseTimeout(Duration.ofSeconds(86400))
                            .setHeartbeatTimeout(Duration.ofSeconds(30))
                            .build());

    private final DeploymentActivities deploymentActivities =
            Workflow.newActivityStub(
                    DeploymentActivities.class,
                    ActivityOptions.newBuilder()
                            .setHeartbeatTimeout(Duration.ofSeconds(30))
                            .setScheduleToCloseTimeout(Duration.ofMinutes(5))
                            .build());
    private WorkerVersionEnablementState state;

    private final AtomicReference<Exception> submitOrderException = new AtomicReference<>();

    @WorkflowInit
    public WorkerVersionEnablementImpl(StartWorkerVersionEnablementRequest request) {
        this.state = WorkerVersionEnablementState.newBuilder().setArgs(request).build();
    }


    @Override
    public void execute(StartWorkerVersionEnablementRequest req) {
        logger.info(
                "Starting enablement demonstration: {} with {} orders at {}/min",
                req.getEnablementId(),
                req.getOrderCount(),
                req.getSubmitRatePerMin());

        var submitScope = Workflow.newCancellationScope(inner -> {
            Async.function(() -> {
                submitOrdersUntilSignal();
                return null;
            }).thenApply(v -> {
                logger.info("Order submissions completed successfully");
                return v;
            }).exceptionally(e -> {
                logger.error("Order submission failed", e);
                submitOrderException.set((Exception) e);
                return null;
            });
        });
        if(submitOrderException.get() != null) {
            logger.error("Order submissions failed", submitOrderException.get());
            return;
        }

        try {
            submitScope.run();
        } catch (Exception e) {
            logger.error("Order submission failed, cancelling scope", e);
            throw e;
        }
        if(state.getDeployRequestsCount() > 0) {
            for(var i = state.getDeployRequestsCount(); i > -1; i--) {
                var deploy = this.state.getDeployRequests(i);
                this.state = this.state.toBuilder().removeDeployRequests(i).build();
                this.state =  this.state.toBuilder().addDeployments(deploymentActivities.deployWorkerVersion(deploy)).build();
            }
        }
        Workflow.await(Workflow::isEveryHandlerFinished);
        Workflow.await(()-> false);
    }

    @Override
    public WorkerVersionEnablementState getState() {
        return state;
    }

    @Override
    public void pause() {
        logger.info("Enablement workflow paused");
    }

    @Override
    public void resume() {
        logger.info("Enablement workflow resumed");
    }

    @Override
    public void deployWorkerVersion(DeployWorkerVersionRequest cmd) {
        this.state = this.state.toBuilder().addDeployRequests(cmd).build();
    }

    private void submitOrdersUntilSignal() {
        // call activity with forever-order-starter
        orderActivities.submitOrders(SubmitOrdersRequest.newBuilder().
                setOrderIdSeed(state.getArgs().getOrderIdSeed()).
                setEnablementId(state.getArgs().getEnablementId()).
                setSubmitRatePerMin(state.getArgs().getSubmitRatePerMin()).build());

    }

}
