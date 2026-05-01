package com.acme.processing;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;

class ProcessingWorkerK8sConfigTest {

    @Test
    void processingWorkerK8sProfileDoesNotOverrideCoreWorkerRegistrations() throws Exception {
        var resource = new ClassPathResource("application-k8s.yaml");
        String yaml = resource.getContentAsString(StandardCharsets.UTF_8);

        assertThat(yaml)
                .contains("file:/etc/config/temporal/temporal-config.yaml")
                .doesNotContain("workers:")
                .doesNotContain("workflow-classes:")
                .doesNotContain("activity-beans:")
                .doesNotContain("nexus-service-beans:");
    }
}
