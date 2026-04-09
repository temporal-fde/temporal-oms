package com.acme.processing.controllers;

import com.acme.processing.services.KafkaConsumer;
import jakarta.annotation.PostConstruct;
import org.springframework.core.io.ClassPathResource;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

@RestController
@RequestMapping("/admin")
public class AdminController {
    private final KafkaConsumer kafkaConsumer;
    // Constructor
    private String orderTemplate;

    @PostConstruct
    public void loadTemplate() throws IOException {
        ClassPathResource resource = new ClassPathResource("templates/displayOrder.html");
        orderTemplate = new String(resource.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
    }

    public AdminController(KafkaConsumer kafkaConsumer) {
        this.kafkaConsumer = kafkaConsumer;
    }

    @GetMapping(value = "/order-fulfillment/{orderId}", produces = "text/html")
    public String getOrder(@PathVariable("orderId") String orderId) {
        String orderResult = kafkaConsumer.getOrder(orderId);
        return String.format(orderTemplate, orderId, orderResult);
    }

}
