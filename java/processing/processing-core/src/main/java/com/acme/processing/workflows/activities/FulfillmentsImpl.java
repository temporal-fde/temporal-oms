package com.acme.processing.workflows.activities;

import com.acme.processing.workflows.OrderImpl;
import com.acme.proto.acme.processing.domain.processing.v1.FulfillOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.FulfillOrderResponse;
import com.google.protobuf.util.JsonFormat;
import io.temporal.failure.ApplicationFailure;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.test.EmbeddedKafkaKraftBroker;
import org.springframework.stereotype.Component;

@Component("fulfillment-activities")
public class FulfillmentsImpl implements Fulfillments{

    private Logger logger = LoggerFactory.getLogger(FulfillmentsImpl.class);
    private final EmbeddedKafkaKraftBroker broker;

    @Value("${kafka.topic}")
    private String kafkaTopic;

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    public FulfillmentsImpl(EmbeddedKafkaKraftBroker broker, KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
        this.broker = broker;
    }

    @Override
    public FulfillOrderResponse fulfillOrder(FulfillOrderRequest cmd) {
        // send message to Kafka for fulfillment


        // Serialize the FulfillOrderRequest to a JSON object for kafka
        try {
            String kafkaRec = JsonFormat.printer()
                    .print(cmd);
            // Use the order_id as the record key
            kafkaTemplate.send(kafkaTopic, cmd.getOrder().getOrderId(), kafkaRec);
            logger.info("Record placed on kafka topic {} broker port {}", kafkaTopic, broker.getBrokersAsString());
            return FulfillOrderResponse.getDefaultInstance();
        }
        catch (Exception e)
        {
            throw ApplicationFailure.newFailure("Failed to serialize FulfillmentRequest", "SerializationError");
        }

    }
}
