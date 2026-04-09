package com.acme.processing.services;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.util.HashMap;

@Service
public class KafkaConsumer {
    HashMap<String,String> orderRecords = new HashMap<>();

    @KafkaListener(topics = {"${spring.kafka.topic}"}, groupId = "${spring.kafka.groupId}")
    public void consume(ConsumerRecord<String, String> record) {
        String orderId = record.key();
        String message = record.value();
        System.out.println("Consuming message -- Key: " + orderId + ", Value: " + message);
        // If key orderId exists, message will be replaced.
        // Probably not good form.
        orderRecords.put(orderId,message);
    }

    public String getOrder(String orderId)
    {
        // returns null if orderId does not exist.
        return (orderRecords.get(orderId));
    }
}
