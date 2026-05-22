package com.acme.enablements.config;

import com.acme.enablements.converters.ProtobufJsonHttpMessageConverter;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.List;

/**
 * Web MVC configuration for Spring Boot application.
 * Registers custom HTTP message converters for protobuf JSON serialization.
 */
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    @Override
    public void extendMessageConverters(List<HttpMessageConverter<?>> converters) {
        converters.add(0, new ProtobufJsonHttpMessageConverter());
    }
}
