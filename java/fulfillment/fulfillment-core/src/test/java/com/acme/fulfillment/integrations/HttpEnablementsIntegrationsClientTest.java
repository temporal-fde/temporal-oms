package com.acme.fulfillment.integrations;

import com.acme.proto.acme.common.v1.Address;
import com.acme.proto.acme.common.v1.EasyPostAddress;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.queryParam;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class HttpEnablementsIntegrationsClientTest {

    @Test
    void verifyAddressEncodesProtobufJsonQueryParameter() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        var client = new HttpEnablementsIntegrationsClient(
                builder,
                new ObjectMapper(),
                "http://enablements.test");

        server.expect(requestTo(org.hamcrest.Matchers.startsWith(
                        "http://enablements.test/api/v1/integrations/shipping/verify-address?request=")))
                .andExpect(queryParam("request", org.hamcrest.Matchers.containsString("%22address%22")))
                .andExpect(queryParam("request", org.hamcrest.Matchers.not(org.hamcrest.Matchers.containsString("%2522address%2522"))))
                .andRespond(withSuccess("""
                        {
                          "address": {
                            "easypost": {
                              "id": "adr_dest_nyc_01",
                              "street1": "11 Wall St",
                              "city": "New York",
                              "state": "NY",
                              "zip": "10005",
                              "country": "US"
                            }
                          }
                        }
                        """, MediaType.APPLICATION_JSON));

        var response = client.verifyAddress(VerifyAddressRequest.newBuilder()
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
        server.verify();
    }
}
