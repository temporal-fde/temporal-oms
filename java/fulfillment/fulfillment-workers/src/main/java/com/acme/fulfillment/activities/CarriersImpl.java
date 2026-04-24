package com.acme.fulfillment.activities;

import com.acme.fulfillment.workflows.activities.Carriers;
import com.acme.proto.acme.common.v1.Address;
import com.acme.proto.acme.common.v1.EasyPostAddress;
import com.acme.proto.acme.common.v1.Money;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.CarrierRate;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.Errors;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetCarrierRatesRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetCarrierRatesResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import com.easypost.exception.APIException;
import com.easypost.exception.EasyPostException;
import com.easypost.model.FieldError;
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
 * All EasyPost shipping operations: address verification, carrier rate queries, and label printing.
 * verifyAddress has a real EasyPost integration; getCarrierRates and printShippingLabel are stubs.
 * Phase 6: replace stubs with real EasyPost Shipment creation and label generation.
 */
@Component("carriersActivities")
public class CarriersImpl implements Carriers {

    private static final Logger logger = LoggerFactory.getLogger(CarriersImpl.class);
    private final EasyPostClient easyPostClient;

    @Autowired(required = false)
    public CarriersImpl(EasyPostClient easyPostClient) {
        this.easyPostClient = easyPostClient;
    }

    @Override
    public VerifyAddressResponse verifyAddress(VerifyAddressRequest request) {
        if (easyPostClient == null) {
            throw ApplicationFailure.newNonRetryableFailure(
                    "EasyPost not configured — set EASYPOST_API_KEY", Errors.ERROR_ADDRESS_VERIFY_FAILED.name());
        }

        var address = request.getAddress();
        var ep = address.getEasypost();

        logger.info("verifyAddress: {}", ep.getStreet1());

        if (address.hasEasypost() && !ep.getId().isEmpty()) {
            return VerifyAddressResponse.newBuilder().setAddress(address).build();
        }

        Map<String, Object> fields = new HashMap<>();
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
                    .setCity(verified.getCity()     != null ? verified.getCity()     : ep.getCity())
                    .setState(verified.getState()    != null ? verified.getState()    : ep.getState())
                    .setZip(verified.getZip()       != null ? verified.getZip()       : ep.getZip())
                    .setCountry(verified.getCountry()  != null ? verified.getCountry()  : ep.getCountry())
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

    @Override
    public GetCarrierRatesResponse getCarrierRates(GetCarrierRatesRequest request) {
        logger.info("getCarrierRates stub: order_id={}, easypost_address_id={}",
                request.getOrderId(), request.getEasypostAddressId());

        var stubRate = CarrierRate.newBuilder()
                .setRateId("rate_stub_" + request.getOrderId())
                .setCarrier("UPS")
                .setServiceLevel("Ground")
                .setCost(Money.newBuilder().setCurrency("USD").setUnits(999L).build())
                .setEstimatedDays(5)
                .build();

        return GetCarrierRatesResponse.newBuilder()
                .setShipmentId("shipment_stub_" + request.getOrderId())
                .addRates(stubRate)
                .build();
    }

    @Override
    public PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request) {
        logger.info("printShippingLabel stub: order_id={}, shipment_id={}, rate_id={}",
                request.getOrderId(), request.getShipmentId(), request.getRateId());

        return PrintShippingLabelResponse.newBuilder()
                .setTrackingNumber("1Z999AA1" + request.getOrderId().replace("-", "").substring(0, 8).toUpperCase())
                .setLabelUrl("https://easypost.com/labels/stub_" + request.getShipmentId() + ".pdf")
                .build();
    }
}
