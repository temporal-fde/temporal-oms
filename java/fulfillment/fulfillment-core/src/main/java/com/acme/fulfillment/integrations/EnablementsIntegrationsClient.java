package com.acme.fulfillment.integrations;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;

public interface EnablementsIntegrationsClient {

    VerifyAddressResponse verifyAddress(VerifyAddressRequest request);

    PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request);
}
