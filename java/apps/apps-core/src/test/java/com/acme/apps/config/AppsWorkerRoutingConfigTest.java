package com.acme.apps.config;

import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;

import java.nio.charset.StandardCharsets;

import static org.assertj.core.api.Assertions.assertThat;

class AppsWorkerRoutingConfigTest {

    @Test
    void appsNoLongerRegistersIntegrationNexusServices() throws Exception {
        var resource = new ClassPathResource("acme.apps.yaml");
        String yaml = resource.getContentAsString(StandardCharsets.UTF_8);

        assertThat(yaml).doesNotContain("- task-queue: integrations");
        assertThat(yaml).doesNotContain("- commerce-app-service");
        assertThat(yaml).doesNotContain("- pims-service");
        assertThat(yaml).doesNotContain("- payments-service");
        assertThat(yaml).doesNotContain("- inventory-service");
    }
}
