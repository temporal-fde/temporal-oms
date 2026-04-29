package com.acme.enablements.integrations;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.DeductInventoryRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.DeductInventoryResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ShippingLineItem;
import com.acme.proto.acme.oms.v1.Order;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.queryParam;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class HttpEnablementsIntegrationsClientTest {

    @Test
    void validateOrderPostsProtobufJsonToCommerceEndpoint() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        var client = new HttpEnablementsIntegrationsClient(
                builder,
                new ObjectMapper(),
                "http://enablements.test");

        server.expect(requestTo("http://enablements.test/api/v1/integrations/commerce-app/validate-order"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(content().string(containsString("\"orderId\": \"order-1\"")))
                .andRespond(withSuccess("""
                        {
                          "order": {
                            "orderId": "order-1"
                          },
                          "manualCorrectionNeeded": true
                        }
                        """, MediaType.APPLICATION_JSON));

        var response = client.validateOrder(ValidateOrderRequest.newBuilder()
                .setOrder(Order.newBuilder().setOrderId("order-1").build())
                .build());

        assertThat(response.getManualCorrectionNeeded()).isTrue();
        assertThat(response.getOrder().getOrderId()).isEqualTo("order-1");
        server.verify();
    }

    @Test
    void enrichOrderUsesSingleEncodedProtobufJsonQueryParameter() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        var client = new HttpEnablementsIntegrationsClient(
                builder,
                new ObjectMapper(),
                "http://enablements.test");

        server.expect(requestTo(org.hamcrest.Matchers.startsWith(
                        "http://enablements.test/api/v1/integrations/pims/enrich-order?request=")))
                .andExpect(method(HttpMethod.GET))
                .andExpect(queryParam("request", containsString("%22order%22")))
                .andExpect(queryParam("request", not(containsString("%2522order%2522"))))
                .andRespond(withSuccess("""
                        {
                          "order": {
                            "orderId": "order-1"
                          },
                          "items": [
                            {
                              "itemId": "ITEM-ELEC-001",
                              "skuId": "ELEC-SKU-001",
                              "brandCode": "NEXGEN",
                              "quantity": 2
                            }
                          ]
                        }
                        """, MediaType.APPLICATION_JSON));

        var response = client.enrichOrder(EnrichOrderRequest.newBuilder()
                .setOrder(Order.newBuilder()
                        .setOrderId("order-1")
                        .addItems(com.acme.proto.acme.oms.v1.Item.newBuilder()
                                .setItemId("ITEM-ELEC-001")
                                .setQuantity(2)
                                .build())
                        .build())
                .build());

        assertThat(response.getItems(0).getSkuId()).isEqualTo("ELEC-SKU-001");
        server.verify();
    }

    @Test
    void inventoryClientRoutesReadAndMutationOperationsToEnablementsApi() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        var client = new HttpEnablementsIntegrationsClient(
                builder,
                new ObjectMapper(),
                "http://enablements.test");

        server.expect(requestTo(org.hamcrest.Matchers.startsWith(
                        "http://enablements.test/api/v1/integrations/inventory/lookup-address?request=")))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withSuccess("""
                        {
                          "address": {
                            "easypost": {
                              "id": "adr_wh_east_01"
                            }
                          }
                        }
                        """, MediaType.APPLICATION_JSON));

        server.expect(requestTo("http://enablements.test/api/v1/integrations/inventory/deduct"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().string(containsString("\"orderId\": \"order-1\"")))
                .andRespond(withSuccess("""
                        {
                          "success": true
                        }
                        """, MediaType.APPLICATION_JSON));

        var lookup = client.lookupInventoryAddress(LookupInventoryAddressRequest.newBuilder()
                .addItems(ShippingLineItem.newBuilder().setSkuId("ELEC-SKU-001").setQuantity(1).build())
                .build());
        var deducted = client.deductInventory(DeductInventoryRequest.newBuilder()
                .setOrderId("order-1")
                .build());

        assertThat(lookup.getAddress().getEasypost().getId()).isEqualTo("adr_wh_east_01");
        assertThat(deducted.getSuccess()).isTrue();
        server.verify();
    }
}
