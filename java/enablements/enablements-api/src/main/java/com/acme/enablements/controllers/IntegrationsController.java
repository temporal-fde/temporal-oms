package com.acme.enablements.controllers;

import com.acme.enablements.integrations.CommerceIntegrationService;
import com.acme.enablements.integrations.EnablementIntegrationsFixturesResponse;
import com.acme.enablements.integrations.IntegrationFixtureException;
import com.acme.enablements.integrations.InventoryIntegrationService;
import com.acme.enablements.integrations.LocationEventsIntegrationService;
import com.acme.enablements.integrations.PimsIntegrationService;
import com.acme.enablements.integrations.ProtobufQueryParser;
import com.acme.enablements.integrations.ShippingFixtureService;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.DeductInventoryRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.DeductInventoryResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetLocationEventsRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetLocationEventsResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetShippingRatesRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetShippingRatesResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.HoldItemsRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.HoldItemsResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReleaseHoldRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReleaseHoldResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReserveItemsRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ReserveItemsResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/integrations")
public class IntegrationsController {

    private final CommerceIntegrationService commerce;
    private final PimsIntegrationService pims;
    private final InventoryIntegrationService inventory;
    private final ShippingFixtureService shipping;
    private final LocationEventsIntegrationService locationEvents;
    private final ProtobufQueryParser queryParser;

    public IntegrationsController(
            CommerceIntegrationService commerce,
            PimsIntegrationService pims,
            InventoryIntegrationService inventory,
            ShippingFixtureService shipping,
            LocationEventsIntegrationService locationEvents,
            ProtobufQueryParser queryParser) {
        this.commerce = commerce;
        this.pims = pims;
        this.inventory = inventory;
        this.shipping = shipping;
        this.locationEvents = locationEvents;
        this.queryParser = queryParser;
    }

    @PostMapping("/commerce-app/validate-order")
    public ValidateOrderResponse validateOrder(@RequestBody ValidateOrderRequest request) {
        return commerce.validateOrder(request);
    }

    @GetMapping("/pims/enrich-order")
    public EnrichOrderResponse enrichOrder(@RequestParam("request") String requestJson) {
        return pims.enrichOrder(queryParser.parse(requestJson, EnrichOrderRequest.class));
    }

    @GetMapping("/inventory/lookup-address")
    public LookupInventoryAddressResponse lookupInventoryAddress(@RequestParam("request") String requestJson) {
        return inventory.lookupInventoryAddress(queryParser.parse(requestJson, LookupInventoryAddressRequest.class));
    }

    @GetMapping("/inventory/alternate-warehouse")
    public FindAlternateWarehouseResponse alternateWarehouse(@RequestParam("request") String requestJson) {
        return inventory.findAlternateWarehouse(queryParser.parse(requestJson, FindAlternateWarehouseRequest.class));
    }

    @GetMapping("/inventory/holds")
    public HoldItemsResponse holdItems(@RequestParam("request") String requestJson) {
        return inventory.holdItems(queryParser.parse(requestJson, HoldItemsRequest.class));
    }

    @GetMapping("/inventory/reservations")
    public ReserveItemsResponse reserveItems(@RequestParam("request") String requestJson) {
        return inventory.reserveItems(queryParser.parse(requestJson, ReserveItemsRequest.class));
    }

    @PostMapping("/inventory/deduct")
    public DeductInventoryResponse deductInventory(@RequestBody DeductInventoryRequest request) {
        return inventory.deductInventory(request);
    }

    @PostMapping("/inventory/release-hold")
    public ReleaseHoldResponse releaseHold(@RequestBody ReleaseHoldRequest request) {
        return inventory.releaseHold(request);
    }

    @GetMapping("/shipping/verify-address")
    public VerifyAddressResponse verifyAddress(@RequestParam("request") String requestJson) {
        return shipping.verifyAddress(queryParser.parse(requestJson, VerifyAddressRequest.class));
    }

    @GetMapping("/shipping/rates")
    public GetShippingRatesResponse getShippingRates(@RequestParam("request") String requestJson) {
        return shipping.getShippingRates(queryParser.parse(requestJson, GetShippingRatesRequest.class));
    }

    @GetMapping("/shipping/labels")
    public PrintShippingLabelResponse printShippingLabel(@RequestParam("request") String requestJson) {
        return shipping.printShippingLabel(queryParser.parse(requestJson, PrintShippingLabelRequest.class));
    }

    @GetMapping("/shipping/fixtures")
    public EnablementIntegrationsFixturesResponse shippingFixtures() {
        return shipping.fixtures();
    }

    @GetMapping("/location-events")
    public GetLocationEventsResponse getLocationEvents(@RequestParam("request") String requestJson) {
        return locationEvents.getLocationEvents(queryParser.parse(requestJson, GetLocationEventsRequest.class));
    }

    @GetMapping("/fixtures")
    public EnablementIntegrationsFixturesResponse allFixtures() {
        return shipping.fixtures();
    }

    @ExceptionHandler(IntegrationFixtureException.class)
    public ResponseEntity<Map<String, String>> handleFixtureException(IntegrationFixtureException e) {
        HttpStatus status = switch (e.getCode()) {
            case ADDRESS_VERIFY_FAILED, BAD_REQUEST -> HttpStatus.BAD_REQUEST;
            case INVALID_RATE, UNKNOWN_ADDRESS, UNKNOWN_SHIPMENT -> HttpStatus.NOT_FOUND;
        };
        return ResponseEntity.status(status)
                .body(Map.of(
                        "code", e.getCode().name(),
                        "message", e.getMessage()));
    }
}
