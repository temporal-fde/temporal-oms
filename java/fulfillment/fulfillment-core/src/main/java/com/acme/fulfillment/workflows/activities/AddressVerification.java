package com.acme.fulfillment.workflows.activities;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

/**
 * AddressVerification activity — resolves and verifies a shipping address via EasyPost.
 *
 * If address.easypost_address is already set on the incoming Address, returns it as-is.
 * Otherwise calls EasyPost AddressService.createAndVerify(Map) and populates
 * easypost_address on the returned Address. The easypost_address.id is stored in
 * workflow state and passed to getCarrierRates when fulfillOrder arrives.
 */
@ActivityInterface
public interface AddressVerification {

    @ActivityMethod
    VerifyAddressResponse verifyAddress(VerifyAddressRequest request);
}
