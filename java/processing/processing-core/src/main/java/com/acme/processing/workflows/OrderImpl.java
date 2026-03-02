package com.acme.processing.workflows;

import com.acme.processing.workflows.activities.CommerceApp;
import com.acme.processing.workflows.activities.Enrichments;
import com.acme.processing.workflows.activities.Fulfillments;
import com.acme.processing.workflows.activities.Support;
import com.acme.proto.acme.processing.domain.processing.v1.*;
import io.temporal.activity.ActivityOptions;
import io.temporal.failure.ActivityFailure;
import io.temporal.workflow.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CancellationException;

/**
 * Implementation of Order Workflow
 *
 * Pattern: Processing Service
 * - Coordinates order processing logic
 * - Uses Updates to manage order lifecycle
 * - Handles order submission, payment capture, and cancellation
 */
public class OrderImpl implements Order {
    private final CommerceApp commerceApp;
    private final Enrichments enrichments;
    private GetProcessOrderStateResponse state;
    private Logger logger = LoggerFactory.getLogger(OrderImpl.class);
    private Fulfillments fulfillments;

    @WorkflowInit
    public OrderImpl(ProcessOrderRequest args) {
        this.state = GetProcessOrderStateResponse.newBuilder().build();
        this.state = this.state.toBuilder().addArgs(args).build();
        this.commerceApp = Workflow.newActivityStub(CommerceApp.class,
                ActivityOptions.newBuilder()
                        // the commerce app API is rate limited
                        // so target this tq that is throttled by Temporal service
                        .setTaskQueue("commerce-app")
                        .setScheduleToCloseTimeout(Duration.ofSeconds(args.getOptions().getProcessingTimeoutSecs()))
                        .setStartToCloseTimeout(Duration.ofSeconds(60)).build());

        this.enrichments = Workflow.newActivityStub(Enrichments.class,
                ActivityOptions.newBuilder()
                        .setScheduleToCloseTimeout(Duration.ofSeconds(60)).build());
        this.fulfillments = Workflow.newActivityStub(Fulfillments.class,
                ActivityOptions.newBuilder()
                        .setScheduleToCloseTimeout(Duration.ofSeconds(60)).build());
    }

    @Override
    public GetProcessOrderStateResponse execute(ProcessOrderRequest request) {
        logger.info("Processing order {}", request);

        // 1. validate order (immediate or async activity)
        // 2. enrich order
        // 3. fulfill order
        // if any of this fails, cancel order with `void` specified for payment
        var scope = Workflow.newCancellationScope(inner-> {
            // this might block for quite some time due to invalid order correction
            var validation = this.commerceApp.validateOrder(ValidateOrderRequest.newBuilder()
                    .setOrder(request.getOrder())
                    .setCustomerId(request.getCustomerId())
                    .setValidationTimeoutSecs(request.getOptions().getProcessingTimeoutSecs()).build());
            // validate the order
            this.state = this.state.toBuilder().setValidation(validation).build();

            if(validation.getManualCorrectionNeeded() || validation.getValidationFailuresCount() > 0) {
                var support = Workflow.newActivityStub(Support.class, ActivityOptions.newBuilder()
                                // we only set the schedule to close timeout here
                                .setScheduleToCloseTimeout(Duration.ofSeconds(request.getOptions().getProcessingTimeoutSecs()))
                                .setTaskQueue("support")
                                .build());
                this.state = this.state.toBuilder().setValidation(support.manuallyValidateOrder(ManuallyValidateOrderRequest.newBuilder()
                        .setOrder(request.getOrder())
                        .setCustomerId(request.getCustomerId())
                        .setWorkflowId(Workflow.getInfo().getWorkflowId())
                        .build())).build();
                if(this.state.getValidation().getValidationFailuresCount() > 0) {
                    // we tried to get manual correction of order but still failed so aborting processing here
                    return;
                }
            }

            // enrich the order
            this.state = this.state.toBuilder().setEnrichment(
                    this.enrichments.enrichOrder(EnrichOrderRequest.newBuilder()
                            .setOrder(request.getOrder()).build())).build();

            // fulfill the order
            this.state = this.state.toBuilder().setFulfillment(this.fulfillments.fulfillOrder(FulfillOrderRequest.newBuilder()
                    .setOrder(request.getOrder()).addAllItems(this.state.getEnrichment().getItemsList()).build())).build();
        });

        Workflow.newTimer(Duration.ofSeconds(request.getOptions().getProcessingTimeoutSecs())).thenApply(result -> {
            if(!state.hasFulfillment()) {
                scope.cancel();
            }
            return null;
        });
        try {
            scope.run();
        } catch (ActivityFailure e) {
            this.state.toBuilder().addErrors(e.getMessage());
            throw e;
        }
        Workflow.await(Workflow::isEveryHandlerFinished);
        return this.state;
    }

    @Override
    public GetProcessOrderStateResponse getState() {
        return this.state;
    }

}