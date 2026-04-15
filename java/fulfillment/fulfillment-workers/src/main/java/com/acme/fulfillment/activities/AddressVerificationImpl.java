package com.acme.fulfillment.activities;

import com.acme.fulfillment.workflows.activities.AddressVerification;
import com.acme.proto.acme.common.v1.EasyPostAddress;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * Stub implementation — returns the address with a placeholder EasyPostAddress.
 * Phase 6: replace with real EasyPost AddressService.createAndVerify(Map) call.
 */
@Component("addressVerificationActivities")
public class AddressVerificationImpl implements AddressVerification {

    private static final Logger logger = LoggerFactory.getLogger(AddressVerificationImpl.class);

    @Override
    public VerifyAddressResponse verifyAddress(VerifyAddressRequest request) {
        logger.info("verifyAddress stub called for address: {}", request.getAddress().getStreet());

        // If already verified, return as-is
        if (request.getAddress().hasEasypostAddress()) {
            return VerifyAddressResponse.newBuilder()
                    .setAddress(request.getAddress())
                    .build();
        }

        // Stub: populate a placeholder EasyPostAddress
        var easyPostAddress = EasyPostAddress.newBuilder()
                .setId("adr_stub_" + request.getAddress().getPostalCode())
                .setResidential(false)
                .setVerified(true)
                .build();

        var verifiedAddress = request.getAddress().toBuilder()
                .setEasypostAddress(easyPostAddress)
                .build();

        return VerifyAddressResponse.newBuilder()
                .setAddress(verifiedAddress)
                .build();
    }
}
