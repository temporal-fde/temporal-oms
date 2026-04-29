package com.acme.enablements.services;

import com.acme.enablements.integrations.EnablementsIntegrationsClient;
import com.acme.oms.services.CommerceAppService;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
import io.nexusrpc.handler.OperationHandler;
import io.nexusrpc.handler.OperationImpl;
import io.nexusrpc.handler.ServiceImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

@Component("commerce-app-service")
@ServiceImpl(service = CommerceAppService.class)
public class CommerceAppServiceImpl {

    private final Logger logger = LoggerFactory.getLogger(CommerceAppServiceImpl.class);
    private final EnablementsIntegrationsClient enablements;

    public CommerceAppServiceImpl(EnablementsIntegrationsClient enablements) {
        this.enablements = enablements;
    }

    @OperationImpl
    public OperationHandler<ValidateOrderRequest, ValidateOrderResponse> validateOrder() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("validateOrder Nexus adapter via enablements-api, orderId={}",
                    request.getOrder().getOrderId());
            return enablements.validateOrder(request);
        });
    }
}
