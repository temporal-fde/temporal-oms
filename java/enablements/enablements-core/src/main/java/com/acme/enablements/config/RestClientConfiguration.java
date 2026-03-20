package com.acme.enablements.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

/**
 * Spring configuration for RestClient used by enablement activities.
 *
 * Provides a RestClient bean configured with:
 * - Base URL to the apps-api service (for order submission)
 * - Timeout and error handling defaults
 */
@Configuration
@ConditionalOnClass(RestClient.class)
public class RestClientConfiguration {

    @Value("${enablements.apps-api.base-url:http://localhost:8080}")
    private String appsApiBaseUrl;

    /**
     * Create a RestClient bean for calling apps-api endpoints.
     *
     * @return configured RestClient instance
     */
    @Bean
    @ConditionalOnMissingBean
    public RestClient restClient() {
        return RestClient.builder()
                .baseUrl(appsApiBaseUrl)
                .build();
    }
}
