package com.acme.fulfillment;

import com.easypost.exception.EasyPostException;
import com.easypost.service.EasyPostClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class EasyPostConfig {

    @Bean
    public EasyPostClient easyPostClient(@Value("${easypost.api-key}") String apiKey) {
        if (apiKey == null || apiKey.isBlank()) {
            throw new IllegalStateException("EASYPOST_API_KEY is required — set it in your environment");
        }
        try {
            return new EasyPostClient(apiKey);
        } catch (EasyPostException e) {
            throw new IllegalStateException("Failed to initialize EasyPost client", e);
        }
    }
}
