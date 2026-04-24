package com.acme.fulfillment.workflows;

import com.acme.fulfillment.workflows.activities.Carriers;
import com.acme.fulfillment.workflows.activities.FulfillmentOptionsLoader;
import com.acme.oms.services.InventoryService;
import com.acme.proto.acme.common.v1.Money;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.*;
import io.temporal.activity.ActivityOptions;
import io.temporal.activity.LocalActivityOptions;
import io.temporal.common.SearchAttributeKey;
import io.temporal.common.VersioningBehavior;
import io.temporal.failure.ApplicationFailure;
import io.temporal.workflow.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.List;
import java.util.Optional;

/**
 * fulfillment.Order Workflow Implementation (V1)
 *
 * Lifecycle:
 *  1. [UpdateWithStart] validateOrder → Carriers.verifyAddress → store verified Address → return
 *  2. execute() unblocks → loadOptions (LocalActivity) → InventoryService.holdItems → await fulfillOrder/cancel/timeout
 *  3. [Update] fulfillOrder → InventoryService.reserveItems → Carriers.getCarrierRates → select rate (margin check)
 *               → concurrent: Carriers.printShippingLabel + InventoryService.deductInventory → await notifyDeliveryStatus
 *  4. [Signal] notifyDeliveryStatus → DELIVERED or CANCELED
 *
 * Compensation: detached scope releases inventory hold via InventoryService on cancelOrder Signal or timeout.
 */
public class OrderImpl implements Order {

    // margin_leak registered in fulfillment namespace as --type Int (maps to Long in Java SDK)
    private static final SearchAttributeKey<Long> MARGIN_LEAK = SearchAttributeKey.forLong("margin_leak");
    private static final long DEFAULT_FULFILLMENT_TIMEOUT_SECS = 86_400L; // 24 hours

    private final Carriers carriers;
    private final FulfillmentOptionsLoader optionsLoader;

    // Initialized in execute() after FulfillmentOptions are loaded (endpoint name needed)
    private InventoryService inventory;

    private GetFulfillmentOrderStateResponse state;
    private boolean cancelFlag = false;
    private boolean fulfillOrderReceived = false;
    private boolean deliveryStatusReceived = false;

    private final Logger logger = LoggerFactory.getLogger(OrderImpl.class);

    @WorkflowInit
    public OrderImpl(StartOrderFulfillmentRequest args) {
        this.state = GetFulfillmentOrderStateResponse.newBuilder()
                .setArgs(args)
                .setStatus(FulfillmentStatus.FULFILLMENT_STATUS_STARTED)
                .build();

        var defaultActivityOptions = ActivityOptions.newBuilder()
                .setStartToCloseTimeout(Duration.ofSeconds(30))
                .build();

        this.carriers = Workflow.newActivityStub(Carriers.class, defaultActivityOptions);
        this.optionsLoader = Workflow.newLocalActivityStub(FulfillmentOptionsLoader.class,
                LocalActivityOptions.newBuilder()
                        .setStartToCloseTimeout(Duration.ofSeconds(5))
                        .build());
    }

    @Override
    @WorkflowVersioningBehavior(VersioningBehavior.PINNED)
    public void execute(StartOrderFulfillmentRequest request) {
        logger.info("fulfillment.Order started for order_id={}", request.getOrderId());

        // Wait for validateOrder Update (delivered as part of UpdateWithStart from apps.Order)
        Workflow.await(() -> state.hasValidatedAddress() || cancelFlag);
        if (cancelFlag) {
            logger.info("Order {} cancelled before address validation", request.getOrderId());
            return;
        }

        // Load fulfillment policy (shipping_margin + integrations_endpoint) via LocalActivity
        var options = optionsLoader.loadOptions(
                LoadFulfillmentOptionsRequest.newBuilder()
                        .setOrderId(request.getOrderId())
                        .build());
        this.state = this.state.toBuilder().setOptions(options).build();

        // Configure InventoryService Nexus stub using the integrations endpoint from options
        this.inventory = Workflow.newNexusServiceStub(InventoryService.class,
                NexusServiceOptions.newBuilder()
                        .setEndpoint(options.getIntegrationsEndpoint())
                        .setOperationOptions(NexusOperationOptions.newBuilder()
                                .setScheduleToCloseTimeout(Duration.ofSeconds(30))
                                .build())
                        .build());

        // Eagerly hold inventory while apps.Order processes the order
        var holdResponse = inventory.holdItems(
                HoldItemsRequest.newBuilder()
                        .setOrderId(request.getOrderId())
                        .addAllItems(extractStartItems(request))
                        .build());

        this.state = this.state.toBuilder()
                .setStatus(FulfillmentStatus.FULFILLMENT_STATUS_VALIDATED)
                .build();

        // Detached scope: releaseHold runs even if the workflow scope is cancelled
        var releaseHoldScope = Workflow.newDetachedCancellationScope(() ->
                inventory.releaseHold(ReleaseHoldRequest.newBuilder()
                        .setOrderId(request.getOrderId())
                        .setHoldId(holdResponse.getHoldId())
                        .build()));

        // Wait for fulfillOrder Update, cancelOrder Signal, or timeout
        long timeoutSecs = (request.hasOptions() && request.getOptions().getFulfillmentTimeoutSecs() > 0)
                ? request.getOptions().getFulfillmentTimeoutSecs()
                : DEFAULT_FULFILLMENT_TIMEOUT_SECS;

        boolean conditionMet = Workflow.await(Duration.ofSeconds(timeoutSecs),
                () -> fulfillOrderReceived || cancelFlag);

        if (!conditionMet || cancelFlag) {
            logger.info("Order {} did not receive fulfillOrder in time or was cancelled — releasing hold",
                    request.getOrderId());
            this.state = this.state.toBuilder()
                    .setStatus(FulfillmentStatus.FULFILLMENT_STATUS_CANCELED)
                    .build();
            releaseHoldScope.run();
            return;
        }

        // fulfillOrder Update has been received; wait for the handler (+ notifyDeliveryStatus) to complete
        Workflow.await(Workflow::isEveryHandlerFinished);
        logger.info("fulfillment.Order complete for order_id={}, status={}",
                request.getOrderId(), state.getStatus());
    }

    // ── validateOrder Update ──────────────────────────────────────────────────

    @Override
    public void validateValidateOrder(ValidateOrderRequest request) {
        if (request.getOrderId().isBlank()) {
            throw new IllegalArgumentException("order_id is required for validateOrder");
        }
        if (!request.hasAddress()) {
            throw new IllegalArgumentException("address is required for validateOrder");
        }
    }

    @Override
    public ValidateOrderResponse validateOrder(ValidateOrderRequest request) {
        logger.info("Verifying address for order_id={}", request.getOrderId());

        var verifyResponse = carriers.verifyAddress(
                VerifyAddressRequest.newBuilder()
                        .setAddress(request.getAddress())
                        .build());

        this.state = this.state.toBuilder()
                .setValidatedAddress(verifyResponse.getAddress())
                .build();

        return ValidateOrderResponse.newBuilder()
                .setAddress(verifyResponse.getAddress())
                .build();
    }

    // ── fulfillOrder Update ───────────────────────────────────────────────────

    @Override
    public void validateFulfillOrder(OrderFulfillRequest request) {
        if (!state.hasValidatedAddress()) {
            throw ApplicationFailure.newNonRetryableFailure(
                    "validateOrder must complete before fulfillOrder can be accepted",
                    "PRECONDITION_FAILED");
        }
        if (!request.hasProcessedOrder()) {
            throw new IllegalArgumentException("processed_order is required for fulfillOrder");
        }
    }

    @Override
    public OrderFulfillResponse fulfillOrder(OrderFulfillRequest request) {
        var orderId = request.getProcessedOrder().getOrderId();
        logger.info("Processing fulfillOrder for order_id={}", orderId);

        this.fulfillOrderReceived = true;
        this.state = this.state.toBuilder()
                .setFulfillmentRequest(request)
                .setStatus(FulfillmentStatus.FULFILLMENT_STATUS_FULFILLING)
                .build();

        // Reserve inventory with warehouse allocations from processing
        var reservation = inventory.reserveItems(
                ReserveItemsRequest.newBuilder()
                        .setOrderId(orderId)
                        .addAllItems(extractProcessedItems(request.getProcessedOrder()))
                        .build());

        // Get carrier rates — creates the EasyPost Shipment using the verified address ID
        var ratesResponse = carriers.getCarrierRates(
                GetCarrierRatesRequest.newBuilder()
                        .setOrderId(orderId)
                        .setEasypostAddressId(state.getValidatedAddress().getEasypost().getId())
                        .addAllItems(extractProcessedItems(request.getProcessedOrder()))
                        .build());

        // Select rate; detect and record margin leakage
        var selection = selectRate(
                ratesResponse,
                state.getArgs().getSelectedShipping(),
                state.getOptions().getShippingMargin());

        if (selection.getMarginDeltaCents() > 0) {
            Workflow.upsertTypedSearchAttributes(MARGIN_LEAK.valueSet(selection.getMarginDeltaCents()));
        }

        this.state = this.state.toBuilder().setShippingSelection(selection).build();

        // Print label and deduct inventory concurrently — independent terminal operations
        var labelPromise = Async.function(carriers::printShippingLabel,
                PrintShippingLabelRequest.newBuilder()
                        .setOrderId(orderId)
                        .setShipmentId(ratesResponse.getShipmentId())
                        .setRateId(selection.getRateId())
                        .build());

        var deductPromise = Async.function(inventory::deductInventory,
                DeductInventoryRequest.newBuilder()
                        .setOrderId(orderId)
                        .setReservationId(reservation.getReservationId())
                        .build());

        Promise.allOf(labelPromise, deductPromise).get();

        var labelResponse = labelPromise.get();
        this.state = this.state.toBuilder()
                .setTrackingNumber(labelResponse.getTrackingNumber())
                .setStatus(FulfillmentStatus.FULFILLMENT_STATUS_COMPLETED)
                .build();

        logger.info("Label printed for order_id={}, tracking_number={}", orderId, labelResponse.getTrackingNumber());

        // Await delivery status signal — DELIVERED or CANCELED
        Workflow.await(() -> deliveryStatusReceived);

        return OrderFulfillResponse.newBuilder()
                .setTrackingNumber(labelResponse.getTrackingNumber())
                .setShippingSelection(selection)
                .build();
    }

    // ── cancelOrder Signal ────────────────────────────────────────────────────

    @Override
    public void cancelOrder(CancelFulfillmentOrderRequest request) {
        logger.info("cancelOrder received for order_id={}: {}", request.getOrderId(), request.getReason());
        this.cancelFlag = true;
    }

    // ── notifyDeliveryStatus Signal ───────────────────────────────────────────

    @Override
    public void notifyDeliveryStatus(DeliveryStatusNotification notification) {
        logger.info("notifyDeliveryStatus for order_id={}: {}",
                notification.getOrderId(), notification.getDeliveryStatus());
        this.deliveryStatusReceived = true;
        this.state = this.state.toBuilder()
                .setDeliveryStatus(notification.getDeliveryStatus())
                .setStatus(notification.getDeliveryStatus() == DeliveryStatus.DELIVERY_STATUS_DELIVERED
                        ? FulfillmentStatus.FULFILLMENT_STATUS_DELIVERED
                        : FulfillmentStatus.FULFILLMENT_STATUS_CANCELED)
                .build();
    }

    // ── getState Query ────────────────────────────────────────────────────────

    @Override
    public GetFulfillmentOrderStateResponse getState() {
        return this.state;
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private ShippingSelection selectRate(GetCarrierRatesResponse ratesResponse,
                                         SelectedShippingOption selected,
                                         Money shippingMargin) {
        List<CarrierRate> rates = ratesResponse.getRatesList();
        if (rates.isEmpty()) {
            throw ApplicationFailure.newNonRetryableFailure("No carrier rates available", "NO_RATES");
        }

        Optional<CarrierRate> originalRate = rates.stream()
                .filter(r -> r.getRateId().equals(selected.getOptionId()))
                .findFirst();

        CarrierRate chosen;
        boolean isFallback = false;
        String fallbackReason = "";

        if (originalRate.isPresent()) {
            chosen = originalRate.get();
        } else {
            long marginUnits = shippingMargin.getUnits();
            chosen = rates.stream()
                    .filter(r -> r.getCost().getUnits() <= marginUnits)
                    .min((a, b) -> Long.compare(a.getCost().getUnits(), b.getCost().getUnits()))
                    .orElseGet(() -> rates.stream()
                            .min((a, b) -> Long.compare(a.getCost().getUnits(), b.getCost().getUnits()))
                            .orElseThrow());
            isFallback = true;
            fallbackReason = "original_option_unavailable";
        }

        long actualCents = chosen.getCost().getUnits();
        long marginCents = shippingMargin.getUnits();
        long delta = Math.max(0L, actualCents - marginCents);

        return ShippingSelection.newBuilder()
                .setOptionId(selected.getOptionId())
                .setRateId(chosen.getRateId())
                .setCarrier(chosen.getCarrier())
                .setServiceLevel(chosen.getServiceLevel())
                .setActualPrice(chosen.getCost())
                .setMarginDeltaCents(delta)
                .setIsFallback(isFallback)
                .setFallbackReason(fallbackReason)
                .build();
    }

    private List<FulfillmentItem> extractStartItems(StartOrderFulfillmentRequest request) {
        return request.getPlacedOrder().getProcessOrder().getOrder().getItemsList().stream()
                .map(item -> FulfillmentItem.newBuilder()
                        .setItemId(item.getItemId())
                        .setQuantity(item.getQuantity())
                        .build())
                .toList();
    }

    private List<FulfillmentItem> extractProcessedItems(ProcessedOrder processedOrder) {
        return processedOrder.getState().getEnrichment().getItemsList().stream()
                .map(item -> FulfillmentItem.newBuilder()
                        .setItemId(item.getItemId())
                        .setSkuId(item.getSkuId())
                        .setBrandCode(item.getBrandCode())
                        .setQuantity(item.getQuantity())
                        .build())
                .toList();
    }
}
