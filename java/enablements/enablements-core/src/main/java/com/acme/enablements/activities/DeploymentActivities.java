package com.acme.enablements.activities;

import com.acme.proto.acme.enablements.v1.DeployWorkerVersionRequest;
import com.acme.proto.acme.enablements.v1.DeployWorkerVersionResponse;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

/**
 * Activities for deploying worker versions and managing version compatibility.
 */
@ActivityInterface
public interface DeploymentActivities {

  /**
   * Deploy v2 workers to the Kubernetes cluster using Temporal Worker Controller.
   * <p>
   * This activity applies the TemporalWorkerDeployment v2 CRD via kubectl,
   * which instructs the Temporal Worker Controller to spin up v2 worker pods.
   *
   * @return
   * @throws RuntimeException if deployment fails or times out
   */
  @ActivityMethod
  DeployWorkerVersionResponse deployWorkerVersion(DeployWorkerVersionRequest cmd);

  /**
   * Register v2 build-id as compatible with v1 in Temporal.
   *
   * This activity configures Temporal's build-id routing so that:
   * - Existing workflows continue on v1
   * - New workflows route to v2
   *
   * @throws RuntimeException if registration fails
   */
  @ActivityMethod
  void registerCompatibility();
}
