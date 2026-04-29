package com.acme.enablements.integrations;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.DeductInventoryRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.DeductInventoryResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.HoldItemsRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.HoldItemsResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReleaseHoldRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReleaseHoldResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReserveItemsRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReserveItemsResponse;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.protobuf.Message;
import com.google.protobuf.util.JsonFormat;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import java.lang.reflect.Method;

@Component
public class HttpEnablementsIntegrationsClient implements EnablementsIntegrationsClient {

    private final RestClient restClient;
    private final ObjectMapper objectMapper;
    private final JsonFormat.Printer printer = JsonFormat.printer().includingDefaultValueFields();
    private final JsonFormat.Parser parser = JsonFormat.parser().ignoringUnknownFields();

    public HttpEnablementsIntegrationsClient(
            RestClient.Builder restClientBuilder,
            ObjectMapper objectMapper,
            @Value("${enablements.api.base-url:http://localhost:8050}") String enablementsApiBaseUrl) {
        this.restClient = restClientBuilder.baseUrl(enablementsApiBaseUrl).build();
        this.objectMapper = objectMapper;
    }

    @Override
    public ValidateOrderResponse validateOrder(ValidateOrderRequest request) {
        return post(
                "/api/v1/integrations/commerce-app/validate-order",
                request,
                ValidateOrderResponse.class);
    }

    @Override
    public EnrichOrderResponse enrichOrder(EnrichOrderRequest request) {
        return get(
                "/api/v1/integrations/pims/enrich-order",
                request,
                EnrichOrderResponse.class);
    }

    @Override
    public LookupInventoryAddressResponse lookupInventoryAddress(LookupInventoryAddressRequest request) {
        return get(
                "/api/v1/integrations/inventory/lookup-address",
                request,
                LookupInventoryAddressResponse.class);
    }

    @Override
    public FindAlternateWarehouseResponse findAlternateWarehouse(FindAlternateWarehouseRequest request) {
        return get(
                "/api/v1/integrations/inventory/alternate-warehouse",
                request,
                FindAlternateWarehouseResponse.class);
    }

    @Override
    public HoldItemsResponse holdItems(HoldItemsRequest request) {
        return get(
                "/api/v1/integrations/inventory/holds",
                request,
                HoldItemsResponse.class);
    }

    @Override
    public ReserveItemsResponse reserveItems(ReserveItemsRequest request) {
        return get(
                "/api/v1/integrations/inventory/reservations",
                request,
                ReserveItemsResponse.class);
    }

    @Override
    public DeductInventoryResponse deductInventory(DeductInventoryRequest request) {
        return post(
                "/api/v1/integrations/inventory/deduct",
                request,
                DeductInventoryResponse.class);
    }

    @Override
    public ReleaseHoldResponse releaseHold(ReleaseHoldRequest request) {
        return post(
                "/api/v1/integrations/inventory/release-hold",
                request,
                ReleaseHoldResponse.class);
    }

    private <T extends Message> T get(String path, Message request, Class<T> responseType) {
        String requestJson = toJson(request);
        try {
            String responseJson = restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path(path)
                            .queryParam("request", "{request}")
                            .build(requestJson))
                    .retrieve()
                    .body(String.class);
            return fromJson(responseJson == null ? "{}" : responseJson, responseType);
        } catch (RestClientResponseException e) {
            throw toClientException(e);
        }
    }

    private <T extends Message> T post(String path, Message request, Class<T> responseType) {
        try {
            String responseJson = restClient.post()
                    .uri(path)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(toJson(request))
                    .retrieve()
                    .body(String.class);
            return fromJson(responseJson == null ? "{}" : responseJson, responseType);
        } catch (RestClientResponseException e) {
            throw toClientException(e);
        }
    }

    private String toJson(Message message) {
        try {
            return printer.print(message);
        } catch (Exception e) {
            throw new IllegalArgumentException("Failed to serialize protobuf request", e);
        }
    }

    @SuppressWarnings("unchecked")
    private <T extends Message> T fromJson(String json, Class<T> responseType) {
        try {
            Method newBuilder = responseType.getMethod("newBuilder");
            Message.Builder builder = (Message.Builder) newBuilder.invoke(null);
            parser.merge(json, builder);
            return (T) builder.build();
        } catch (Exception e) {
            throw new IllegalStateException("Failed to parse protobuf response: " + responseType.getName(), e);
        }
    }

    private EnablementsIntegrationClientException toClientException(RestClientResponseException e) {
        String code = "";
        String message = e.getMessage();
        try {
            JsonNode body = objectMapper.readTree(e.getResponseBodyAsString());
            code = body.path("code").asText("");
            message = body.path("message").asText(message);
        } catch (Exception ignored) {
            // Keep the original HTTP exception message when the body is not the enablements error DTO.
        }
        return new EnablementsIntegrationClientException(
                e.getStatusCode().value(),
                code,
                message,
                e);
    }
}
