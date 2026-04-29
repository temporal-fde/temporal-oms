package com.acme.enablements.integrations;

import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class CommerceIntegrationService {

    private static final Logger logger = LoggerFactory.getLogger(CommerceIntegrationService.class);

    public ValidateOrderResponse validateOrder(ValidateOrderRequest request) {
        boolean invalid = request.getOrder().getOrderId().contains("invalid");
        logger.info("validateOrder orderId={}, invalid={}", request.getOrder().getOrderId(), invalid);
        return ValidateOrderResponse.newBuilder()
                .setOrder(request.getOrder())
                .setManualCorrectionNeeded(invalid)
                .build();
    }
}
