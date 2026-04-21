package com.acme.enablements.activities;

import com.acme.proto.acme.apps.api.orders.v1.MakePaymentRequest;
import com.acme.proto.acme.apps.api.orders.v1.Metadata;
import com.acme.proto.acme.apps.api.orders.v1.Order;
import com.acme.proto.acme.common.v1.Address;
import com.acme.proto.acme.apps.api.orders.v1.SubmitOrderRequest;
import com.acme.proto.acme.enablements.v1.SubmitOrdersRequest;
import com.acme.proto.acme.enablements.v1.SubmitOrdersResponse;
import com.google.protobuf.util.JsonFormat;
import io.temporal.activity.Activity;
import io.temporal.client.ActivityCompletionException;
import io.temporal.failure.CanceledFailure;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Component("order-activities")
public class OrderActivitiesImpl implements OrderActivities {

    private static final Logger logger = LoggerFactory.getLogger(OrderActivitiesImpl.class);

    private final RestClient appsRestClient;
    private final RestClient processingRestClient;

    public OrderActivitiesImpl(
            RestClient.Builder restClientBuilder,
            @Value("${enablements.apps-api.base-url:http://localhost:8080}") String appsApiBaseUrl,
            @Value("${enablements.processing-api.base-url:http://localhost:8081}") String processingApiBaseUrl) {
        this.appsRestClient = restClientBuilder.baseUrl(appsApiBaseUrl).build();
        this.processingRestClient = restClientBuilder.baseUrl(processingApiBaseUrl).build();
    }

    @Override
    public SubmitOrdersResponse submitOrders(SubmitOrdersRequest cmd) {
        var ctx = Activity.getExecutionContext();
        var sleepIntervalMs = (60 / cmd.getSubmitRatePerMin()) * 1000;
        var canceled = false;
        var submittedCount = 0;
        List<String> submittedOrderIds = new ArrayList<>();

        while (!canceled) {
            try {
                ctx.heartbeat(null);
                var enablementId = cmd.getEnablementId().isBlank() ? ctx.getInfo().getWorkflowId() : cmd.getEnablementId();

                // Generate order ID as enablement_id + timestamp
                long timestamp = System.currentTimeMillis();
                String orderId = cmd.getOrderIdSeed() + "-" + enablementId + "-" + timestamp;

                try {
                    // Call /api/v1/orders/{orderId} endpoint
                    callOrderEndpoint(orderId);
                    callPaymentEndpoint(orderId);
                    if(cmd.getOrderIdSeed().contains("invalid")) {
                        scheduleValidation(orderId);
                    }

                    submittedOrderIds.add(orderId);
                    submittedCount++;
                    logger.debug("Submitted order: {} (total: {})", orderId, submittedCount);
                } catch (Exception e) {
                    logger.error("Failed to submit order {}: {}", orderId, e.getMessage());
                    throw e;
                }

                try {
                    Thread.sleep(sleepIntervalMs);
                } catch (InterruptedException e) {
                    if (e.getCause() instanceof CanceledFailure) {
                        canceled = true;
                    }
                }
            } catch (ActivityCompletionException e) {
                logger.error("Activity failed: {}", e.getMessage());
                if (e.getCause() instanceof CanceledFailure) {
                    logger.info("Activity canceled");
                    canceled = true;
                } else {
                    throw e;
                }
            }
        }

        logger.info("Order submission activity completed. Submitted {} orders", submittedCount);
        return SubmitOrdersResponse.newBuilder()
                .setOrdersSubmittedCount(String.valueOf(submittedCount))
                .build();
    }

    private void callOrderEndpoint(String orderId) {
        var shippingAddress = Address.newBuilder()
                .setEasypost(com.acme.proto.acme.common.v1.EasyPostAddress.newBuilder()
                        .setStreet1(orderId + "-street-" + UUID.randomUUID())
                        .setCity(orderId + "-city-" + UUID.randomUUID().toString().substring(0, 8))
                        .setState(orderId + "-state")
                        .setZip(orderId + "-" + System.currentTimeMillis())
                        .setCountry("US"))
                .build();

        var item = com.acme.proto.acme.apps.api.orders.v1.Item.newBuilder()
                .setItemId(orderId + "-item-" + UUID.randomUUID().toString().substring(0, 8))
                .setQuantity((int) (Math.random() * 10) + 1)
                .build();

        var order = Order.newBuilder()
                .setOrderId(orderId)
                .addItems(item)
                .setShippingAddress(shippingAddress)
                .build();

        var req = SubmitOrderRequest.newBuilder()
                .setCustomerId("enablements")
                .setOrder(order)
                .build();

        try {
            String body = JsonFormat.printer().print(req);
            appsRestClient.put()
                .uri("/api/v1/commerce-app/orders/{orderId}", orderId)
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .onStatus(status -> status.value() != 202,
                        (request, response) -> {
                            throw new RuntimeException("Failed to submit order " + orderId +
                                    ": expected 202 Accepted, got " + response.getStatusCode());
                        })
                .body(Void.class);
        } catch (Exception e) {
            throw new RuntimeException("Failed to serialize or submit order " + orderId, e);
        }
    }

    private void callPaymentEndpoint(String orderId) {
        var req = MakePaymentRequest.newBuilder()
                .setCustomerId("enablements")
                .setRrn(UUID.randomUUID().toString())
                .setAmountCents((long) (Math.random() * 10000) + 100)
                .setMetadata(Metadata.newBuilder().setOrderId(orderId).build())
                .build();

        try {
            String body = JsonFormat.printer().print(req);
            appsRestClient.post()
                .uri("/api/v1/payments-app/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .onStatus(status -> status.value() != 202,
                        (request, response) -> {
                            throw new RuntimeException("Failed to capture payment for order " + orderId +
                                    ": expected 202 Accepted, got " + response.getStatusCode());
                        })
                .body(Void.class);
        } catch (Exception e) {
            throw new RuntimeException("Failed to serialize or capture payment for order " + orderId, e);
        }
    }

    private void scheduleValidation(String orderId) {
        Thread.ofVirtual().start(() -> {
            try {
                Thread.sleep(40_000);
                processingRestClient.post()
                    .uri("/api/v1/validations/{orderId}/complete", orderId)
                    .retrieve()
                    .onStatus(status -> status.value() != 202,
                            (request, response) -> {
                                throw new RuntimeException("Failed to complete validation for order " + orderId +
                                        ": expected 202 Accepted, got " + response.getStatusCode());
                            })
                    .body(Void.class);
                logger.debug("Validation completed for order: {}", orderId);
            } catch (Exception e) {
                logger.error("Failed to complete validation for order {}: {}", orderId, e.getMessage());
            }
        });
    }
}
