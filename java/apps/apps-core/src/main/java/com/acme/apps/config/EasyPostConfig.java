package com.acme.apps.config;

import com.easypost.service.EasyPostClient;
import com.easypost.exception.EasyPostException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class EasyPostConfig {

    @Bean
    @ConditionalOnProperty(name = "easypost.api-key")
    public EasyPostClient easyPostClient(@Value("${easypost.api-key}") String apiKey) {
        try {
            return new EasyPostClient(apiKey);
        } catch (EasyPostException e) {
            throw new RuntimeException("Failed to initialize EasyPost client", e);
        }
    }
}
