package com.acme.processing.controllers;

import com.acme.processing.services.KafkaConsumer;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/admin")
public class AdminController {
    private final KafkaConsumer kafkaConsumer;

    public AdminController(KafkaConsumer kafkaConsumer) {
        this.kafkaConsumer = kafkaConsumer;
    }

    @GetMapping(value = "/order-fulfillment/{orderId}", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<String> getOrder(@PathVariable String orderId) {
        try {
            String orderResult = kafkaConsumer.getOrder(orderId);
            if (orderResult == null) {
                String safe = orderId.replace("\\", "\\\\").replace("\"", "\\\"");
                return ResponseEntity.status(404)
                        .body("{\"error\":\"Order " + safe + " not found\"}");
            }
            return ResponseEntity.ok(orderResult);
        } catch (Exception e) {
            String safe = e.getMessage() == null ? "unknown error" : e.getMessage().replace("\\", "\\\\").replace("\"", "\\\"");
            return ResponseEntity.status(500)
                    .body("{\"error\":\"" + safe + "\"}");
        }
    }

}