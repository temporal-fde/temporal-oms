package com.acme.fulfillment.activities;

import com.acme.fulfillment.workflows.activities.AddressVerification;
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
    public AddressVerificationImpl(EasyPostClient easyPostClient) {
        this.easyPostClient = easyPostClient;
    }

    @Override
    public VerifyAddressResponse verifyAddress(VerifyAddressRequest request) {
        var address = request.getAddress();

        logger.info("verifyAddress called for address: {}", address.getStreet());

        // If already verified by EasyPost, return as-is
        if (address.hasEasypostAddress()) {
            return VerifyAddressResponse.newBuilder()
                    .setAddress(address)
                    .build();
        }

        Map<String, Object> addressFields = new HashMap<>();
        addressFields.put("street1", address.getStreet());
        addressFields.put("city", address.getCity());
        addressFields.put("state", address.getState());
        addressFields.put("zip", address.getPostalCode());
        addressFields.put("country", address.getCountry());

        try {
            com.easypost.model.Address verifiedAddressResponse = easyPostClient.address.createAndVerify(addressFields);

            boolean isVerified = verifiedAddressResponse.getVerifications() != null
                    && verifiedAddressResponse.getVerifications().getDelivery() != null
                    && Boolean.TRUE.equals(verifiedAddressResponse.getVerifications().getDelivery().getSuccess());

            Boolean residential = verifiedAddressResponse.getResidential();

            var easyPostAddress = EasyPostAddress.newBuilder()
                    .setId(verifiedAddressResponse.getId())
                    .setResidential(Boolean.TRUE.equals(residential))
                    .setVerified(isVerified)
                    .build();

            // return the verified address
            var verifiedAddress = address.toBuilder()
                    .setStreet(verifiedAddressResponse.getStreet1())
                    .setCity(verifiedAddressResponse.getCity())
                    .setState(verifiedAddressResponse.getState())
                    .setPostalCode(verifiedAddressResponse.getZip())
                    .setCountry(verifiedAddressResponse.getCountry())
                    .setEasypostAddress(easyPostAddress)
                    .build();

            logger.info("verifyAddress succeeded: easypost_id={}, verified={}, residential={}",
                    verifiedAddressResponse.getId(), isVerified, residential);

            return VerifyAddressResponse.newBuilder()
                    .setAddress(verifiedAddress)
                    .build();

        } catch (EasyPostException e) {
                String addressError = "undefined";
                String failedField = "undefined";

                // Get the detailed error from the errors object.
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
