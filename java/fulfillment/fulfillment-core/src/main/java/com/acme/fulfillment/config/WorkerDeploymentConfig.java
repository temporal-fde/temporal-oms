package com.acme.fulfillment.config;

import io.temporal.spring.boot.TemporalOptionsCustomizer;
import io.temporal.worker.WorkerDeploymentOptions;
import io.temporal.worker.WorkerOptions;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Centralises Temporal worker deployment options so every worker registered in this
 * context shares the same deployment-series name and build ID. Adding a new task queue
 * worker to acme.fulfillment.yaml automatically inherits these options — no per-worker
 * repetition required.
 */
@Configuration
public class WorkerDeploymentConfig {

    @Bean
    public TemporalOptionsCustomizer<WorkerOptions.Builder> workerDeploymentCustomizer(
            @Value("${TEMPORAL_DEPLOYMENT_NAME:fulfillment}") String deploymentName,
            @Value("${TEMPORAL_WORKER_BUILD_ID:local}") String buildId) {
        var deploymentOptions = WorkerDeploymentOptions.newBuilder()
                .setDeploymentSeriesName(deploymentName)
                .setBuildId(buildId)
                .build();
        return builder -> builder.setDeploymentOptions(deploymentOptions);
    }
}
