package com.acme.processing;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

/**
 * REST API server for the Processing namespace.
 * Exposes controllers and Swagger/OpenAPI documentation.
 * Workers are disabled in this mode.
 */
@SpringBootApplication
@ComponentScan({"com.acme.processing", "com.acme.config"})
public class ApiApplication {

    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(ApiApplication.class);
        app.run(args);
    }
}
