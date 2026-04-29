package com.acme.fulfillment.integrations;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.protobuf.Message;
import com.google.protobuf.util.JsonFormat;
import org.springframework.beans.factory.annotation.Value;
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
    public VerifyAddressResponse verifyAddress(VerifyAddressRequest request) {
        return get(
                "/api/v1/integrations/shipping/verify-address",
                request,
                VerifyAddressResponse.class);
    }

    @Override
    public PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request) {
        return get(
                "/api/v1/integrations/shipping/labels",
                request,
                PrintShippingLabelResponse.class);
    }

    private <T extends Message> T get(String path, Message request, Class<T> responseType) {
        String requestJson = toJson(request);
        try {
            String responseJson = restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path(path)
                            .queryParam("request", requestJson)
                            .build())
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
