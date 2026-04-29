package com.acme.enablements.services;

import com.acme.enablements.integrations.EnablementsIntegrationsClient;
import com.acme.oms.services.ProductInformationManagementService;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderResponse;
import io.nexusrpc.handler.OperationHandler;
import io.nexusrpc.handler.OperationImpl;
import io.nexusrpc.handler.ServiceImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

@Component("pims-service")
@ServiceImpl(service = ProductInformationManagementService.class)
public class ProductInformationManagementServiceImpl {

    private final Logger logger = LoggerFactory.getLogger(ProductInformationManagementServiceImpl.class);
    private final EnablementsIntegrationsClient enablements;

    public ProductInformationManagementServiceImpl(EnablementsIntegrationsClient enablements) {
        this.enablements = enablements;
    }

    @OperationImpl
    public OperationHandler<EnrichOrderRequest, EnrichOrderResponse> enrichOrder() {
        return OperationHandler.sync((ctx, details, request) -> {
            logger.info("enrichOrder Nexus adapter via enablements-api, orderId={}",
                    request.getOrder().getOrderId());
            return enablements.enrichOrder(request);
        });
    }
}
