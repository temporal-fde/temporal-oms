package com.acme.processing.workflows.activities;

import com.acme.proto.acme.processing.domain.processing.v1.FulfillOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.FulfillOrderResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.protobuf.InvalidProtocolBufferException;
import com.google.protobuf.util.JsonFormat;
import io.temporal.failure.ApplicationFailure;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationContextInitializedEvent;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.test.EmbeddedKafkaKraftBroker;
import org.springframework.stereotype.Component;

import static com.acme.proto.acme.processing.domain.processing.v1.Errors.ERRORS_INVALID_ARGUMENTS;
import static com.acme.proto.acme.processing.domain.processing.v1.Errors.ERRORS_KAFKA_ERROR;

@Component("fulfillment-activities")
public class FulfillmentsImpl implements Fulfillments{

    private static final Logger logger = LoggerFactory.getLogger(FulfillmentsImpl.class);
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final EmbeddedKafkaKraftBroker broker;
    private final String kafkaTopic;

    public FulfillmentsImpl(EmbeddedKafkaKraftBroker broker, KafkaTemplate<String, String> kafkaTemplate, @Value("${spring.kafka.topic}") String kafkaTopic) {
        this.kafkaTemplate = kafkaTemplate;
        this.broker = broker;
        this.kafkaTopic = kafkaTopic;

    }

    @Override
    public FulfillOrderResponse fulfillOrder(FulfillOrderRequest cmd) {
        // send message to Kafka for fulfillment
        // Serialize the FulfillOrderRequest to a JSON object for kafka
        try {
            // Mka sure can serialize teh FulfillOrderRequest
            String kafkaRec = JsonFormat.printer()
                    .print(cmd);
            // Use the order_id as the record key
            kafkaTemplate.send(kafkaTopic, cmd.getOrder().getOrderId(), kafkaRec);
            logger.info("Record placed on kafka topic {} broker port {}", kafkaTopic, broker.getBrokersAsString());
            return FulfillOrderResponse.getDefaultInstance();
        } catch (InvalidProtocolBufferException e) {
            // failed to serialize
            throw ApplicationFailure.newNonRetryableFailureWithCause("Failed to serialize FulfillOrderRequest for kafka", ERRORS_INVALID_ARGUMENTS.name(), e);
        }
        catch (Exception e)
        {
            // failed to send for some other reason
            throw ApplicationFailure.newFailureWithCause("Failed to publish FulfillOrderRequest to kafka topic " + kafkaTopic, ERRORS_KAFKA_ERROR.name(), e);
        }

    }
}
