package com.acme.processing.kafka;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.kafka.core.DefaultKafkaProducerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.core.ProducerFactory;
import org.springframework.kafka.test.EmbeddedKafkaKraftBroker;

import java.util.HashMap;
import java.util.Map;

    @Configuration
    public class KafkaConfig {

        @Bean(destroyMethod = "destroy")
        public EmbeddedKafkaKraftBroker embeddedKafkaKraftBroker() throws Exception {
            EmbeddedKafkaKraftBroker broker = new EmbeddedKafkaKraftBroker(1, 1);
            // Starts the broker
            broker.afterPropertiesSet();
            return broker;
        }

        @Bean
        public ProducerFactory<String, String> producerFactory(EmbeddedKafkaKraftBroker broker) {
            Map<String, Object> props = new HashMap<>();
            props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, broker.getBrokersAsString());
            props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
            props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
            return new DefaultKafkaProducerFactory<>(props);
        }

        @Bean
        public KafkaTemplate<String, String> kafkaTemplate(ProducerFactory<String, String> pf) {
            return new KafkaTemplate<>(pf);
        }

    }

