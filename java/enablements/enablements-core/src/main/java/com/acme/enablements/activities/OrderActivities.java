package com.acme.enablements.activities;

import com.acme.proto.acme.enablements.v1.SubmitOrdersRequest;
import com.acme.proto.acme.enablements.v1.SubmitOrdersResponse;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

/**
 * Activities for submitting orders to the OMS during enablement demonstrations.
 */
@ActivityInterface
public interface OrderActivities {

  /**
   * Submit a single order to the OMS via apps-api.
   * <p>
   * This activity calls the apps-api endpoint to create an order, simulating
   * an external client making order submissions. The order flows through the
   * OMS's normal processing pipelines (enrichment, payment capture).
   *
   * @return Order ID if successful
   * @throws RuntimeException if order submission fails after retries
   */
  @ActivityMethod
  SubmitOrdersResponse submitOrders(SubmitOrdersRequest cmd);


}
