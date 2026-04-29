package com.acme.enablements.services;

import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;

import java.nio.charset.StandardCharsets;

import static org.assertj.core.api.Assertions.assertThat;

class EnablementsWorkerRoutingConfigTest {

    @Test
    void enablementsRegistersIntegrationsTaskQueueWithoutPayments() throws Exception {
        var resource = new ClassPathResource("acme.enablements.yaml");
        String yaml = resource.getContentAsString(StandardCharsets.UTF_8);

        assertThat(yaml).contains("- task-queue: integrations");
        assertThat(yaml).contains("- commerce-app-service");
        assertThat(yaml).contains("- pims-service");
        assertThat(yaml).contains("- inventory-service");
        assertThat(yaml).doesNotContain("- payments-service");
    }
}
