package com.acme.fulfillment.workflows.activities;

import com.acme.fulfillment.integrations.EnablementsIntegrationClientException;
import com.acme.fulfillment.integrations.EnablementsIntegrationsClient;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.Errors;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import io.temporal.failure.ApplicationFailure;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * Fixture-backed address verification and label printing through enablements-api.
 */
@Component("carriersActivities")
public class CarriersImpl implements Carriers {

    private static final Logger logger = LoggerFactory.getLogger(CarriersImpl.class);

    private final EnablementsIntegrationsClient enablements;

    public CarriersImpl(EnablementsIntegrationsClient enablements) {
        this.enablements = enablements;
    }

    // ── verifyAddress ─────────────────────────────────────────────────────────

    @Override
    public VerifyAddressResponse verifyAddress(VerifyAddressRequest request) {
        try {
            logger.info("verifyAddress via enablements-api");
            return enablements.verifyAddress(request);
        } catch (EnablementsIntegrationClientException e) {
            if (e.getStatusCode() < 500) {
                throw ApplicationFailure.newNonRetryableFailureWithCause(
                        e.getMessage(),
                        Errors.ERROR_ADDRESS_VERIFY_FAILED.name(),
                        e);
            }
            throw ApplicationFailure.newFailureWithCause(
                    "Enablements API address verification failed: " + e.getMessage(),
                    "SHIPPING_INTEGRATION_FAILED",
                    e);
        } catch (RuntimeException e) {
            throw ApplicationFailure.newFailureWithCause(
                    "Enablements API address verification failed: " + e.getMessage(),
                    "SHIPPING_INTEGRATION_FAILED",
                    e);
        }
    }

    // ── printShippingLabel ────────────────────────────────────────────────────

    @Override
    public PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request) {
        try {
            logger.info("printShippingLabel via enablements-api: shipment_id={}, rate_id={}",
                    request.getShipmentId(), request.getRateId());
            return enablements.printShippingLabel(request);
        } catch (EnablementsIntegrationClientException e) {
            if (e.getStatusCode() == 404 || e.getStatusCode() == 400) {
                throw ApplicationFailure.newNonRetryableFailureWithCause(
                        e.getMessage(),
                        Errors.ERROR_INVALID_RATE.name(),
                        e);
            }
            throw ApplicationFailure.newFailureWithCause(
                    "Failed to print label for shipment " + request.getShipmentId() + ": " + e.getMessage(),
                    "LABEL_PRINT_FAILED",
                    e);
        } catch (RuntimeException e) {
            throw ApplicationFailure.newFailureWithCause(
                    "Failed to print label for shipment " + request.getShipmentId() + ": " + e.getMessage(),
                    "LABEL_PRINT_FAILED", e);
        }
    }
}
