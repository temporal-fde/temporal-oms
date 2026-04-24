package com.acme.fulfillment.activities;

import com.acme.fulfillment.workflows.activities.AddressVerification;
import com.acme.proto.acme.common.v1.Address;
import com.acme.proto.acme.common.v1.EasyPostAddress;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import com.easypost.model.FieldError;
import com.easypost.service.EasyPostClient;
import com.easypost.exception.APIException;
import com.easypost.exception.EasyPostException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import io.temporal.failure.ApplicationFailure;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.Errors;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component("addressVerificationActivities")
public class AddressVerificationImpl implements AddressVerification {

    private static final Logger logger = LoggerFactory.getLogger(AddressVerificationImpl.class);
    private final EasyPostClient easyPostClient;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    public AddressVerificationImpl(EasyPostClient easyPostClient) {
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

        logger.info("verifyAddress called for address: {}", ep.getStreet1());

        // If already verified by EasyPost (id is present), return as-is
        if (address.hasEasypost() && !ep.getId().isEmpty()) {
            return VerifyAddressResponse.newBuilder()
                    .setAddress(address)
                    .build();
        }

        Map<String, Object> addressFields = new HashMap<>();
        addressFields.put("street1", ep.getStreet1());
        addressFields.put("city",    ep.getCity());
        addressFields.put("state",   ep.getState());
        addressFields.put("zip",     ep.getZip());
        addressFields.put("country", ep.getCountry());

        try {
            com.easypost.model.Address verifiedAddressResponse = easyPostClient.address.createAndVerify(addressFields);

            boolean isVerified = verifiedAddressResponse.getVerifications() != null
                    && verifiedAddressResponse.getVerifications().getDelivery() != null
                    && Boolean.TRUE.equals(verifiedAddressResponse.getVerifications().getDelivery().getSuccess());

            Boolean residential = verifiedAddressResponse.getResidential();

            var easyPostAddress = EasyPostAddress.newBuilder()
                    .setId(verifiedAddressResponse.getId())
                    .setStreet1(verifiedAddressResponse.getStreet1() != null ? verifiedAddressResponse.getStreet1() : ep.getStreet1())
                    .setCity(verifiedAddressResponse.getCity()    != null ? verifiedAddressResponse.getCity()    : ep.getCity())
                    .setState(verifiedAddressResponse.getState()   != null ? verifiedAddressResponse.getState()   : ep.getState())
                    .setZip(verifiedAddressResponse.getZip()     != null ? verifiedAddressResponse.getZip()     : ep.getZip())
                    .setCountry(verifiedAddressResponse.getCountry() != null ? verifiedAddressResponse.getCountry() : ep.getCountry())
                    .setResidential(Boolean.TRUE.equals(residential))
                    .build();

            var verifiedAddress = Address.newBuilder()
                    .setEasypost(easyPostAddress)
                    .build();

            logger.info("verifyAddress succeeded: easypost_id={}, verified={}, residential={}",
                    verifiedAddressResponse.getId(), isVerified, residential);

            return VerifyAddressResponse.newBuilder()
                    .setAddress(verifiedAddress)
                    .build();

        } catch (EasyPostException e) {
                String addressError = "undefined";
                String failedField = "undefined";

                List<?> errors = ((APIException) e).getErrors();
                if (errors != null && !errors.isEmpty()) {
                    FieldError fieldError = (FieldError) errors.getFirst();
                    failedField = fieldError.getField();
                    addressError = fieldError.getMessage();
                }

            throw ApplicationFailure.newNonRetryableFailureWithCause(addressError + ". Error with field '" + failedField + "'", Errors.ERROR_ADDRESS_VERIFY_FAILED.name(), e);
        }
    }
}
