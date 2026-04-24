package com.acme.config;

import com.easypost.exception.EasyPostException;
import com.easypost.service.EasyPostClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnExpression;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class EasyPostConfig {

    @Bean
    @ConditionalOnExpression("T(org.springframework.util.StringUtils).hasText('${easypost.api-key:}')")
    public EasyPostClient easyPostClient(@Value("${easypost.api-key}") String apiKey) {
        try {
            return new EasyPostClient(apiKey);
        } catch (EasyPostException e) {
            throw new RuntimeException("Failed to initialize EasyPost client", e);
        }
    }
}
