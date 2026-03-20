package com.acme.enablements;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

/**
 * Temporal worker for the Enablements namespace.
 * Processes worker version enablement workflows and activities.
 * REST API is disabled in this mode.
 */
@SpringBootApplication
@ComponentScan({"com.acme.enablements", "com.acme.config"})
public class WorkerApplication {

    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(WorkerApplication.class);
        app.run(args);
    }
}
