package com.acme.apps;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

/**
 * Temporal worker for the Apps namespace.
 * Processes workflows and activities.
 * REST API is disabled in this mode.
 */
@SpringBootApplication
@ComponentScan({"com.acme.apps", "com.acme.config"})
public class WorkerApplication {

    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(WorkerApplication.class);
        app.run(args);
    }
}
