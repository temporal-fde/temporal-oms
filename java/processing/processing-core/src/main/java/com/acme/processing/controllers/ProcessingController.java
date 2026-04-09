package com.acme.processing.controllers;

import com.acme.processing.services.KafkaConsumer;
import jakarta.annotation.PostConstruct;
import org.springframework.core.io.ClassPathResource;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

@RestController
@RequestMapping("/kafka")
public class ProcessingController {
    private final KafkaConsumer kafkaConsumer;
    // Constructor
    private String orderTemplate;

    @PostConstruct
    public void loadTemplate() throws IOException {
        ClassPathResource resource = new ClassPathResource("templates/displayOrder.html");
        orderTemplate = new String(resource.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
    }

    public ProcessingController(KafkaConsumer kafkaConsumer) {
        this.kafkaConsumer = kafkaConsumer;
    }

    @GetMapping(value = "/fulfillment/{orderId}", produces = "text/html")
    public String getOrder(@PathVariable("orderId") String orderId) {
        String orderResult = kafkaConsumer.getOrder(orderId);
        return String.format(orderTemplate, orderId, orderResult);
    }

}
