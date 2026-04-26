package com.acme.fulfillment.workflows.activities;

import com.acme.proto.acme.common.v1.Address;
import com.acme.proto.acme.common.v1.EasyPostAddress;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.Errors;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import com.easypost.exception.APIException;
import com.easypost.exception.EasyPostException;
import com.easypost.model.FieldError;
import com.easypost.model.Rate;
import com.easypost.model.Shipment;
import com.easypost.service.EasyPostClient;
import io.temporal.failure.ApplicationFailure;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * EasyPost address verification and label printing.
 * Requires EASYPOST_API_KEY — use an EZT-prefixed test key to avoid purchasing real labels.
 */
@Component("carriersActivities")
public class CarriersImpl implements Carriers {

    private static final Logger logger = LoggerFactory.getLogger(CarriersImpl.class);

    @Autowired
    private EasyPostClient easyPostClient;

    // ── verifyAddress ─────────────────────────────────────────────────────────

    @Override
    public VerifyAddressResponse verifyAddress(VerifyAddressRequest request) {

        var address = request.getAddress();
        var ep = address.getEasypost();

        logger.info("verifyAddress: {}", ep.getStreet1());

        if (address.hasEasypost() && !ep.getId().isEmpty()) {
            return VerifyAddressResponse.newBuilder().setAddress(address).build();
        }

        Map<String, Object> fields = new HashMap<>();
        fields.put("name",    request.getCustomerId());
        fields.put("street1", ep.getStreet1());
        fields.put("city",    ep.getCity());
        fields.put("state",   ep.getState());
        fields.put("zip",     ep.getZip());
        fields.put("country", ep.getCountry());

        try {
            com.easypost.model.Address verified = easyPostClient.address.createAndVerify(fields);

            boolean isVerified = verified.getVerifications() != null
                    && verified.getVerifications().getDelivery() != null
                    && Boolean.TRUE.equals(verified.getVerifications().getDelivery().getSuccess());

            var easyPostAddress = EasyPostAddress.newBuilder()
                    .setId(verified.getId())
                    .setStreet1(verified.getStreet1() != null ? verified.getStreet1() : ep.getStreet1())
                    .setCity(verified.getCity()       != null ? verified.getCity()    : ep.getCity())
                    .setState(verified.getState()     != null ? verified.getState()   : ep.getState())
                    .setZip(verified.getZip()         != null ? verified.getZip()     : ep.getZip())
                    .setCountry(verified.getCountry() != null ? verified.getCountry() : ep.getCountry())
                    .setResidential(Boolean.TRUE.equals(verified.getResidential()))
                    .build();

            logger.info("verifyAddress succeeded: easypost_id={}, verified={}", verified.getId(), isVerified);

            return VerifyAddressResponse.newBuilder()
                    .setAddress(Address.newBuilder().setEasypost(easyPostAddress).build())
                    .build();

        } catch (EasyPostException e) {
            String addressError = "undefined";
            String failedField  = "undefined";
            List<?> errors = ((APIException) e).getErrors();
            if (errors != null && !errors.isEmpty()) {
                FieldError fieldError = (FieldError) errors.getFirst();
                failedField  = fieldError.getField();
                addressError = fieldError.getMessage();
            }
            throw ApplicationFailure.newNonRetryableFailureWithCause(
                    addressError + ". Error with field '" + failedField + "'",
                    Errors.ERROR_ADDRESS_VERIFY_FAILED.name(), e);
        }
    }

    // ── printShippingLabel ────────────────────────────────────────────────────

    @Override
    public PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request) {

        try {
            Shipment shipment = easyPostClient.shipment.retrieve(request.getShipmentId());

            logger.info("printShippingLabel: shipment_id={}, status={}", shipment.getId(), shipment.getStatus());

            Rate matchedRate = null;
            for (Rate r : shipment.getRates()) {
                logger.info("Available rate: id={}, carrier={}, service={}", r.getId(), r.getCarrier(), r.getService());
                if (r.getId().equals(request.getRateId())) {
                    matchedRate = r;
                }
            }

            if (matchedRate == null) {
                throw ApplicationFailure.newNonRetryableFailureWithCause(
                        "Rate " + request.getRateId() + " not found on shipment " + request.getShipmentId(),
                        Errors.ERROR_INVALID_RATE.name(),
                        new IllegalArgumentException("rate_id not present in shipment rates"));
            }

            logger.info("printShippingLabel: buying rate={} ({} {})", matchedRate.getId(), matchedRate.getCarrier(), matchedRate.getService());

            Map<String, Object> buyParams = new HashMap<>();
            buyParams.put("rate", Map.of("id", matchedRate.getId()));
            Shipment purchased = easyPostClient.shipment.buy(request.getShipmentId(), buyParams, null);

            String trackingNumber = purchased.getTrackingCode() != null ? purchased.getTrackingCode() : "";
            String labelUrl = purchased.getPostageLabel() != null
                    ? purchased.getPostageLabel().getLabelUrl()
                    : "";

            logger.info("printShippingLabel: order_id={}, tracking={}", request.getOrderId(), trackingNumber);

            return PrintShippingLabelResponse.newBuilder()
                    .setTrackingNumber(trackingNumber)
                    .setLabelUrl(labelUrl)
                    .build();

        } catch (EasyPostException e) {
            if (e instanceof APIException ae) {
                logger.error("EasyPost buy failed: status={}, code={}, message={}",
                        ae.getStatusCode(), ae.getCode(), ae.getMessage());
                if (ae.getErrors() != null) {
                    for (Object err : ae.getErrors()) {
                        if (err instanceof FieldError fe) {
                            logger.error("  field={}, message={}", fe.getField(), fe.getMessage());
                        } else {
                            logger.error("  error detail: {}", err);
                        }
                    }
                }
            } else {
                logger.error("EasyPost error purchasing label: {}", e.getMessage());
            }
            throw ApplicationFailure.newFailureWithCause(
                    "Failed to purchase label for shipment " + request.getShipmentId(),
                    "LABEL_PRINT_FAILED", e);
        }
    }
}
