package com.acme.fulfillment.workflows.activities;

import com.acme.fulfillment.integrations.EnablementsIntegrationClientException;
import com.acme.fulfillment.integrations.EnablementsIntegrationsClient;
import com.acme.proto.acme.common.v1.Address;
import com.acme.proto.acme.common.v1.EasyPostAddress;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import io.temporal.failure.ApplicationFailure;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CarriersImplTest {

    private final Carriers carriers = new CarriersImpl(new FakeEnablementsClient());

    @Test
    void verifyAddressUsesFixtureCatalog() {
        var response = carriers.verifyAddress(VerifyAddressRequest.newBuilder()
                .setCustomerId("customer-1")
                .setAddress(Address.newBuilder()
                        .setEasypost(EasyPostAddress.newBuilder()
                                .setStreet1("11 Wall St")
                                .setCity("New York")
                                .setState("NY")
                                .setZip("10005")
                                .setCountry("US")
                                .build())
                        .build())
                .build());

        assertThat(response.getAddress().getEasypost().getId()).isEqualTo("adr_dest_nyc_01");
    }

    @Test
    void printShippingLabelUsesDeterministicFixtureResponse() {
        var request = PrintShippingLabelRequest.newBuilder()
                .setOrderId("order-1")
                .setShipmentId("shp_adr_wh_east_01_to_adr_dest_nyc_01")
                .setRateId("rate_wh_east_01_nyc_ground")
                .build();

        var response = carriers.printShippingLabel(request);

        assertThat(response.getTrackingNumber()).startsWith("1ZFIXTURE");
        assertThat(response.getLabelUrl()).contains("rate_wh_east_01_nyc_ground");
    }

    @Test
    void invalidRateFailsNonRetryably() {
        var request = PrintShippingLabelRequest.newBuilder()
                .setOrderId("order-1")
                .setShipmentId("shp_adr_wh_east_01_to_adr_dest_nyc_01")
                .setRateId("rate_missing")
                .build();

        assertThatThrownBy(() -> carriers.printShippingLabel(request))
                .isInstanceOf(ApplicationFailure.class)
                .extracting("type")
                .isEqualTo("ERROR_INVALID_RATE");
    }

    private static final class FakeEnablementsClient implements EnablementsIntegrationsClient {
        @Override
        public VerifyAddressResponse verifyAddress(VerifyAddressRequest request) {
            return VerifyAddressResponse.newBuilder()
                    .setAddress(Address.newBuilder()
                            .setEasypost(request.getAddress().getEasypost().toBuilder()
                                    .setId("adr_dest_nyc_01")
                                    .build())
                            .build())
                    .build();
        }

        @Override
        public PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request) {
            if ("rate_missing".equals(request.getRateId())) {
                throw new EnablementsIntegrationClientException(
                        404,
                        "INVALID_RATE",
                        "Rate not found",
                        new IllegalArgumentException("missing rate"));
            }
            return PrintShippingLabelResponse.newBuilder()
                    .setTrackingNumber("1ZFIXTURETEST")
                    .setLabelUrl("https://example.invalid/labels/"
                            + request.getShipmentId() + "/" + request.getRateId() + ".pdf")
                    .build();
        }
    }
}
