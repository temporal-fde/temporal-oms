package com.acme.apps.controllers;

import com.acme.apps.workflows.Order;
import com.acme.proto.acme.apps.api.orders.v1.*;
import com.google.protobuf.Timestamp;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.temporal.api.enums.v1.WorkflowIdConflictPolicy;
import io.temporal.api.enums.v1.WorkflowIdReusePolicy;
import io.temporal.client.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;

/**
 * Commerce App Webhook Controller
 *
 * Receives webhooks from external commerce application
 * Uses UpdateWithStart pattern to send commerce data to CompleteOrder workflow
 *
 * URI Template: /api/v1/commerce-app/orders/{orderId}
 */
@RestController
@RequestMapping("/api/v1/commerce-app")
@Tag(name = "Commerce Webhooks", description = "Webhook endpoints for commerce app integration")
//@SecurityRequirement(name = "ApiKeyAuth")
public class CommerceWebhookController {

    private static final Logger logger = LoggerFactory.getLogger(CommerceWebhookController.class);

    private final WorkflowClient workflowClient;

    public CommerceWebhookController(WorkflowClient workflowClient) {
        this.workflowClient = workflowClient;
    }

    /**
     * Submit commerce order data
     *
     * URI Template: PUT /api/v1/commerce-app/orders/{orderId}
     */
    @PutMapping("/orders/{orderId}")
    @Operation(
        summary = "Submit commerce order",
        description = "Receives commerce order data from external commerce app and sends to CompleteOrder workflow using UpdateWithStart"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "202", description = "Order data accepted",
            content = @Content(schema = @Schema(implementation = SubmitOrderResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid request body"),
        @ApiResponse(responseCode = "401", description = "Missing or invalid API key"),
        @ApiResponse(responseCode = "409", description = "Commerce data already submitted for this order")
    })
    public ResponseEntity<SubmitOrderResponse> submitCommerceOrder(
            @Parameter(description = "Order ID", required = true)
            @PathVariable String orderId,
            @RequestBody SubmitOrderRequest request) {

        logger.info("Received commerce order for orderId: {}", orderId);

        try {
            // Prepare update request using protobuf builders
            var updateRequest = com.acme.proto.acme.apps.domain.apps.v1.SubmitOrderRequest.newBuilder()
                .setOrder(
                    com.acme.proto.acme.oms.v1.Order.newBuilder()
                        .setOrderId(request.getOrder().getOrderId())
                        .addAllItems(request.getOrder().getItemsList().stream()
                            .map(item -> com.acme.proto.acme.oms.v1.Item.newBuilder()
                                .setItemId(item.getItemId())
                                .setQuantity(item.getQuantity())
                                .build())
                            .toList())
                        .setShippingAddress(
                            com.acme.proto.acme.oms.v1.ShippingAddress.newBuilder()
                                .setStreet(request.getOrder().getShippingAddress().getStreet())
                                .setCity(request.getOrder().getShippingAddress().getCity())
                                .setState(request.getOrder().getShippingAddress().getState())
                                .setPostalCode(request.getOrder().getShippingAddress().getPostalCode())
                                .setCountry(request.getOrder().getShippingAddress().getCountry())
                                .build())
                        .build())
                .build();

            // Prepare workflow start request
            Instant now = Instant.now();
            var completeOrderRequest = com.acme.proto.acme.apps.domain.apps.v1.CompleteOrderRequest.newBuilder()
                .setOrderId(orderId)
                .setCustomerId(request.getCustomerId())
                .setTimestamp(Timestamp.newBuilder()
                    .setSeconds(now.getEpochSecond())
                    .setNanos(now.getNano())
                    .build())
                .build();

            // Get workflow stub for method references
            Order workflow = workflowClient.newWorkflowStub(
                Order.class,
                WorkflowOptions.newBuilder()
                    .setWorkflowId(orderId)
                        .setWorkflowIdConflictPolicy(WorkflowIdConflictPolicy.WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING)
                        .setWorkflowIdReusePolicy(WorkflowIdReusePolicy.WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE_FAILED_ONLY)
                    .setTaskQueue("apps")
                    .build()
            );

            // StartUpdateWithStart: atomically start workflow and execute update in one operation
            WorkflowClient.startUpdateWithStart(
                workflow::submitOrder,
                updateRequest,
                UpdateOptions.<com.acme.proto.acme.apps.domain.apps.v1.SubmitOrderRequest>newBuilder()
                        .setWaitForStage(WorkflowUpdateStage.ACCEPTED)
                        .build(),
                new WithStartWorkflowOperation<>(
                    workflow::execute,
                    completeOrderRequest
                )
            );

            logger.info("Commerce order submitted successfully for orderId: {}", orderId);

            Instant responseTime = Instant.now();
            var response = SubmitOrderResponse.newBuilder()
                .setOrderId(orderId)
                .setStatus("accepted")
                .setCreatedAt(Timestamp.newBuilder()
                    .setSeconds(responseTime.getEpochSecond())
                    .setNanos(responseTime.getNano())
                    .build())
                .build();

            return ResponseEntity.accepted().body(response);

        } catch (WorkflowUpdateException e) {
            logger.error("Failed to submit commerce order: {}", e.getMessage(), e);
            Instant errorTime = Instant.now();
            var errorResponse = SubmitOrderResponse.newBuilder()
                .setOrderId(orderId)
                .setStatus("failed")
                .setCreatedAt(Timestamp.newBuilder()
                    .setSeconds(errorTime.getEpochSecond())
                    .setNanos(errorTime.getNano())
                    .build())
                .build();
            return ResponseEntity.status(HttpStatus.CONFLICT).body(errorResponse);
        } catch (Exception e) {
            logger.error("Unexpected error submitting commerce order: {}", e.getMessage(), e);
            Instant errorTime = Instant.now();
            var errorResponse = SubmitOrderResponse.newBuilder()
                .setOrderId(orderId)
                .setStatus("error")
                .setCreatedAt(Timestamp.newBuilder()
                    .setSeconds(errorTime.getEpochSecond())
                    .setNanos(errorTime.getNano())
                    .build())
                .build();
            return ResponseEntity.badRequest().body(errorResponse);
        }
    }

    /**
     * Get list of clothing items
     *
     * URI Template: GET /api/v1/commerce-app/clothing{?limit}
     */
    @GetMapping("/clothing")
    @Operation(
        summary = "List clothing items",
        description = "Returns a list of available clothing items for the shopping interface"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "List of clothing items",
            content = @Content(schema = @Schema(implementation = ListProductsResponse.class)))
    })
    public ResponseEntity<ListProductsResponse> listClothing(
            @Parameter(description = "Maximum number of items to return")
            @RequestParam(defaultValue = "50") int limit) {

        logger.info("Fetching {} clothing items", limit);

        // Mock catalog with 50 items
        String[] categories = {"T-Shirt", "Jeans", "Jacket", "Sweater", "Hoodie", "Dress", "Skirt", "Shorts", "Pants", "Shirt"};
        String[] colors = {"Blue", "Black", "White", "Red", "Green", "Gray", "Navy", "Brown", "Beige", "Pink"};

        java.util.Random random = new java.util.Random();

        var responseBuilder = ListProductsResponse.newBuilder();

        for (int i = 1; i <= Math.min(limit, 50); i++) {
            String category = categories[i % categories.length];
            String color = colors[i % colors.length];
            String name = color + " " + category;
            String description = "Premium " + color.toLowerCase() + " " + category.toLowerCase() + " with modern fit";
            long price = (random.nextInt(50) + 20) * 100; // $20-$70

            responseBuilder.addItems(Product.newBuilder()
                .setItemId("item-" + i)
                .setName(name)
                .setDescription(description)
                .setPriceCents(price)
                .setImageUrl("/images/item-" + i + ".jpg")
                .build());
        }

        return ResponseEntity.ok(responseBuilder.build());
    }

    /**
     * Get orders for customer
     *
     * URI Template: GET /api/v1/commerce-app/orders{?customerId}
     */
    @GetMapping("/orders")
    @Operation(
        summary = "List customer orders",
        description = "Returns orders for the specified customer"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "List of orders",
            content = @Content(schema = @Schema(implementation = ListOrdersResponse.class))),
        @ApiResponse(responseCode = "400", description = "Missing customerId parameter")
    })
    public ResponseEntity<ListOrdersResponse> listOrders(
            @Parameter(description = "Customer ID", required = true)
            @RequestParam String customerId) {

        logger.info("Fetching orders for customer: {}", customerId);

        // TODO: Query actual orders from Temporal workflow queries or database
        // For now, return empty list
        var response = ListOrdersResponse.newBuilder().build();

        return ResponseEntity.ok(response);
    }
}