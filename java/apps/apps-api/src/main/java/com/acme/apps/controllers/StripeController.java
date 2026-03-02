package com.acme.apps.controllers;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * Stripe Integration Controller
 *
 * Handles Stripe payment intent creation and webhook processing
 */
@RestController
@RequestMapping("/api/v1/stripe")
@Tag(name = "Stripe Integration", description = "Stripe payment integration endpoints")
public class StripeController {

    private static final Logger logger = LoggerFactory.getLogger(StripeController.class);

    /**
     * Create Stripe payment intent
     *
     * URI Template: POST /api/v1/stripe/payment-intent
     */
    @PostMapping("/payment-intent")
    @Operation(
        summary = "Create payment intent",
        description = "Creates a Stripe payment intent for the order"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Payment intent created",
            content = @Content(schema = @Schema(implementation = PaymentIntentResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid request")
    })
    public ResponseEntity<PaymentIntentResponse> createPaymentIntent(
            @RequestBody PaymentIntentRequest request) {

        logger.info("Creating payment intent for order: {} amount: {}",
            request.orderId, request.amountCents);

        // TODO: Integrate with actual Stripe SDK
        // For now, return mock client secret
        String clientSecret = "pi_test_" + request.orderId + "_secret_" + System.currentTimeMillis();

        return ResponseEntity.ok(new PaymentIntentResponse(clientSecret));
    }

    /**
     * Stripe webhook handler
     *
     * Receives webhook events from Stripe (payment success, etc.)
     */
    @PostMapping("/webhook")
    @Operation(
        summary = "Stripe webhook",
        description = "Receives webhook events from Stripe"
    )
    public ResponseEntity<Void> handleWebhook(
            @RequestHeader("Stripe-Signature") String signature,
            @RequestBody String payload) {

        logger.info("Received Stripe webhook");

        // TODO: Verify signature and process webhook
        // Extract payment_intent and order_id from metadata
        // Send to PaymentsWebhookController

        return ResponseEntity.ok().build();
    }

    // DTOs
    public record PaymentIntentRequest(
        String orderId,
        long amountCents
    ) {}

    public record PaymentIntentResponse(
        String clientSecret
    ) {}
}