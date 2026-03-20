package com.acme.enablements.activities;

import com.acme.proto.acme.apps.api.orders.v1.Order;
import com.acme.proto.acme.apps.api.orders.v1.ShippingAddress;
import com.acme.proto.acme.apps.api.orders.v1.SubmitOrderRequest;
import com.acme.proto.acme.enablements.v1.SubmitOrdersRequest;
import com.acme.proto.acme.enablements.v1.SubmitOrdersResponse;
import io.temporal.activity.Activity;
import io.temporal.client.ActivityCompletionException;
import io.temporal.failure.CanceledFailure;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.client.RestClient;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class OrderActivitiesImpl implements OrderActivities {

    private static final Logger logger = LoggerFactory.getLogger(OrderActivitiesImpl.class);

    private final RestClient restClient;

    public OrderActivitiesImpl(RestClient restClient) {
        this.restClient = restClient;
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

                // Generate order ID as enablement_id + timestamp
                long timestamp = System.currentTimeMillis();
                String orderId = cmd.getEnablementId() + "-" + timestamp;

                try {
                    // Call /api/v1/orders/{orderId} endpoint
                    callOrderEndpoint(orderId);
                    submittedOrderIds.add(orderId);
                    submittedCount++;
                    logger.debug("Submitted order: {} (total: {})", orderId, submittedCount);
                } catch (Exception e) {
                    logger.warn("Failed to submit order {}: {}", orderId, e.getMessage());
                    canceled = true;
                }

                try {
                    Thread.sleep(sleepIntervalMs);
                } catch (InterruptedException e) {
                    if (e.getCause() instanceof CanceledFailure) {
                        canceled = true;
                    }
                }
            } catch (ActivityCompletionException e) {
                canceled = true;
            }
        }

        logger.info("Order submission activity completed. Submitted {} orders", submittedCount);
        return SubmitOrdersResponse.newBuilder()
                .setOrdersSubmittedCount(String.valueOf(submittedCount))
                .build();
    }

    private void callOrderEndpoint(String orderId) {
        var shippingAddress = ShippingAddress.newBuilder()
                .setStreet(orderId + "-street-" + UUID.randomUUID())
                .setCity(orderId + "-city-" + UUID.randomUUID().toString().substring(0, 8))
                .setState(orderId + "-state")
                .setPostalCode(orderId + "-" + System.currentTimeMillis())
                .setCountry("US")
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

        restClient.put()
                .uri("/api/v1/orders/{orderId}", orderId)
                .body(req)
                .retrieve()
                .onStatus(status -> status.value() != 202,
                        (request, response) -> {
                            throw new RuntimeException("Failed to submit order " + orderId +
                                    ": expected 202 Accepted, got " + response.getStatusCode());
                        })
                .body(Void.class);
    }
}
