package com.acme.enablements.integrations;

import com.acme.proto.acme.common.v1.Address;
import com.acme.proto.acme.common.v1.Coordinate;
import com.acme.proto.acme.common.v1.EasyPostAddress;
import com.acme.proto.acme.common.v1.Money;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.CarrierRate;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FulfillmentItem;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetCarrierRatesRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetCarrierRatesResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetShippingRatesRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetShippingRatesResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ShippingOption;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;

@Service
public class ShippingFixtureService {

    private static final String DEFAULT_FIXTURE_PATH = "classpath:/fixtures/shipping-fixtures.json";

    private final ShippingFixture fixture;
    private final Map<String, ShippingFixture.AddressFixture> addressesById;
    private final Map<String, ShippingFixture.AddressFixture> addressesByKey;
    private final Map<String, ShippingFixture.ShipmentFixture> shipmentsById;
    private final Map<String, ShippingFixture.ShipmentFixture> shipmentsByPair;

    public ShippingFixtureService(
            @Value("${workshop.integrations.shipping.fixture-path:" + DEFAULT_FIXTURE_PATH + "}")
            String fixturePath,
            ResourceLoader resourceLoader,
            ObjectMapper objectMapper) {
        this.fixture = loadFixture(fixturePath, resourceLoader, objectMapper);
        this.addressesById = indexAddressesById(fixture);
        this.addressesByKey = indexAddressesByKey(fixture);
        this.shipmentsById = indexShipmentsById(fixture);
        this.shipmentsByPair = indexShipmentsByPair(fixture);
    }

    public EnablementIntegrationsFixturesResponse fixtures() {
        return new EnablementIntegrationsFixturesResponse(
                fixture.warehouses(),
                fixture.addresses(),
                fixture.shipments().stream()
                        .map(shipment -> new EnablementIntegrationsFixturesResponse.ShipmentState(
                                shipment.shipmentId(),
                                shipment.fromAddressId(),
                                shipment.toAddressId(),
                                shipment.parcel(),
                                shipment.rates(),
                                labelsForShipment(shipment)))
                        .toList(),
                fixture.locationEvents());
    }

    public ShippingFixture shippingFixture() {
        return fixture;
    }

    public ShippingFixture.LocationEventsFixture locationEventsFixture() {
        return fixture.locationEvents();
    }

    public List<ShippingFixture.WarehouseFixture> warehouses() {
        return fixture.warehouses();
    }

    public Optional<Address> addressById(String addressId) {
        var address = addressesById.get(addressId);
        return address == null ? Optional.empty() : Optional.of(toAddress(address));
    }

    public VerifyAddressResponse verifyAddress(VerifyAddressRequest request) {
        if (!request.hasAddress() || !request.getAddress().hasEasypost()) {
            throw new IntegrationFixtureException(
                    IntegrationFixtureException.Code.ADDRESS_VERIFY_FAILED,
                    "address.easypost is required for fixture address verification");
        }

        var input = request.getAddress().getEasypost();
        var fixtureAddress = lookupAddress(input)
                .orElseThrow(() -> new IntegrationFixtureException(
                        IntegrationFixtureException.Code.ADDRESS_VERIFY_FAILED,
                        "No fixture address matched " + addressDescription(input)));

        return VerifyAddressResponse.newBuilder()
                .setAddress(toAddress(fixtureAddress))
                .build();
    }

    public GetShippingRatesResponse getShippingRates(GetShippingRatesRequest request) {
        var shipment = resolveShipment(request)
                .orElseThrow(() -> new IntegrationFixtureException(
                        IntegrationFixtureException.Code.UNKNOWN_SHIPMENT,
                        shipmentNotFoundMessage(request)));

        var response = GetShippingRatesResponse.newBuilder()
                .setShipmentId(shipment.shipmentId());

        for (int i = 0; i < shipment.rates().size(); i++) {
            response.addOptions(toShippingOption(shipment.shipmentId(), shipment.rates().get(i), request, i));
        }

        return response.build();
    }

    public GetCarrierRatesResponse getCarrierRates(GetCarrierRatesRequest request) {
        if (request.getEasypostAddressId().isBlank()) {
            throw new IntegrationFixtureException(
                    IntegrationFixtureException.Code.BAD_REQUEST,
                    "easypost_address_id is required");
        }

        var originAddressId = resolveOriginForItems(request.getItemsList())
                .orElseThrow(() -> new IntegrationFixtureException(
                        IntegrationFixtureException.Code.UNKNOWN_SHIPMENT,
                        "No fixture warehouse can fulfill carrier-rate request items"));

        var shipment = findShipment(originAddressId, request.getEasypostAddressId())
                .orElseThrow(() -> new IntegrationFixtureException(
                        IntegrationFixtureException.Code.UNKNOWN_SHIPMENT,
                        "No fixture shipment for " + originAddressId + " -> " + request.getEasypostAddressId()));

        var response = GetCarrierRatesResponse.newBuilder()
                .setShipmentId(shipment.shipmentId());
        for (var rate : shipment.rates()) {
            response.addRates(CarrierRate.newBuilder()
                    .setRateId(rate.rateId())
                    .setCarrier(defaultString(rate.carrier()))
                    .setServiceLevel(defaultString(rate.serviceLevel()))
                    .setCost(toMoney(rate.cost()))
                    .setEstimatedDays(defaultInt(rate.estimatedDays(), 0))
                    .build());
        }
        return response.build();
    }

    public PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request) {
        var shipment = shipmentsById.get(request.getShipmentId());
        if (shipment == null) {
            throw new IntegrationFixtureException(
                    IntegrationFixtureException.Code.UNKNOWN_SHIPMENT,
                    "Shipment not found in fixtures: " + request.getShipmentId());
        }

        boolean rateExists = shipment.rates().stream()
                .anyMatch(rate -> rate.rateId().equals(request.getRateId()));
        if (!rateExists) {
            throw new IntegrationFixtureException(
                    IntegrationFixtureException.Code.INVALID_RATE,
                    "Rate " + request.getRateId() + " not found on shipment " + request.getShipmentId());
        }

        var label = shipment.labels().stream()
                .filter(candidate -> candidate.rateId().equals(request.getRateId()))
                .findFirst()
                .orElseGet(() -> synthesizedLabel(request.getShipmentId(), request.getRateId()));

        return PrintShippingLabelResponse.newBuilder()
                .setTrackingNumber(label.trackingNumber())
                .setLabelUrl(label.labelUrl())
                .build();
    }

    private Optional<String> resolveOriginForItems(List<FulfillmentItem> items) {
        String skuId = items.isEmpty() ? "" : items.getFirst().getSkuId();
        return fixture.warehouses().stream()
                .filter(warehouse -> handlesSku(warehouse, skuId))
                .map(ShippingFixture.WarehouseFixture::addressId)
                .findFirst();
    }

    private Optional<ShippingFixture.ShipmentFixture> resolveShipment(GetShippingRatesRequest request) {
        if (request.hasSelectedShipment()
                && request.getSelectedShipment().hasEasypost()
                && !request.getSelectedShipment().getEasypost().getShipmentId().isBlank()
                && (request.getFromEasypostId().isBlank() || request.getToEasypostId().isBlank())) {
            return Optional.ofNullable(shipmentsById.get(request.getSelectedShipment().getEasypost().getShipmentId()));
        }
        if (request.getFromEasypostId().isBlank() || request.getToEasypostId().isBlank()) {
            throw new IntegrationFixtureException(
                    IntegrationFixtureException.Code.BAD_REQUEST,
                    "from_easypost_id and to_easypost_id are required unless selected_shipment.easypost.shipment_id is provided");
        }
        return findShipment(request.getFromEasypostId(), request.getToEasypostId());
    }

    private Optional<ShippingFixture.ShipmentFixture> findShipment(String fromAddressId, String toAddressId) {
        return Optional.ofNullable(shipmentsByPair.get(pairKey(fromAddressId, toAddressId)));
    }

    private Optional<ShippingFixture.AddressFixture> lookupAddress(EasyPostAddress input) {
        if (!input.getId().isBlank()) {
            return Optional.ofNullable(addressesById.get(input.getId()));
        }
        return Optional.ofNullable(addressesByKey.get(addressKey(
                input.getStreet1(),
                input.getStreet2(),
                input.getCity(),
                input.getState(),
                input.getZip(),
                input.getCountry())));
    }

    private ShippingOption toShippingOption(
            String shipmentId,
            ShippingFixture.RateFixture rate,
            GetShippingRatesRequest request,
            int index) {
        return ShippingOption.newBuilder()
                .setId(rate.rateId())
                .setCarrier(defaultString(rate.carrier()))
                .setServiceLevel(defaultString(rate.serviceLevel()))
                .setCost(toScenarioMoney(rate.cost(), request, index))
                .setEstimatedDays(toScenarioEstimatedDays(rate, request))
                .setRateId(rate.rateId())
                .setShipmentId(shipmentId)
                .build();
    }

    private Money toScenarioMoney(
            ShippingFixture.MoneyFixture money,
            GetShippingRatesRequest request,
            int index) {
        if (isMarginSpikeTrigger(request)) {
            long units = Math.max(defaultLong(money == null ? null : money.units(), 0L), 2_500L + (index * 375L));
            return Money.newBuilder()
                    .setCurrency(money == null || money.currency() == null ? "USD" : money.currency())
                    .setUnits(units)
                    .build();
        }
        return toMoney(money);
    }

    private int toScenarioEstimatedDays(ShippingFixture.RateFixture rate, GetShippingRatesRequest request) {
        int days = defaultInt(rate.estimatedDays(), 0);
        if (isSlaBreachTrigger(request)) {
            return Math.max(days, 1);
        }
        return days;
    }

    private boolean isMarginSpikeTrigger(GetShippingRatesRequest request) {
        return request.hasSelectedShipment()
                && request.getSelectedShipment().hasPaidPrice()
                && request.getSelectedShipment().getPaidPrice().getUnits() == 1L;
    }

    private boolean isSlaBreachTrigger(GetShippingRatesRequest request) {
        return request.hasSelectedShipment()
                && request.getSelectedShipment().hasEasypost()
                && request.getSelectedShipment().getEasypost().hasSelectedRate()
                && request.getSelectedShipment().getEasypost().getSelectedRate().hasDeliveryDays()
                && request.getSelectedShipment().getEasypost().getSelectedRate().getDeliveryDays() == 0L;
    }

    private List<ShippingFixture.LabelFixture> labelsForShipment(ShippingFixture.ShipmentFixture shipment) {
        return shipment.rates().stream()
                .map(rate -> shipment.labels().stream()
                        .filter(label -> label.rateId().equals(rate.rateId()))
                        .findFirst()
                        .orElseGet(() -> synthesizedLabel(shipment.shipmentId(), rate.rateId())))
                .toList();
    }

    private ShippingFixture.LabelFixture synthesizedLabel(String shipmentId, String rateId) {
        String digest = sha256Hex(shipmentId + ":" + rateId).substring(0, 16).toUpperCase(Locale.ROOT);
        String tracking = "1ZFIXTURE" + digest;
        String encodedShipment = URLEncoder.encode(shipmentId, StandardCharsets.UTF_8);
        String encodedRate = URLEncoder.encode(rateId, StandardCharsets.UTF_8);
        return new ShippingFixture.LabelFixture(
                rateId,
                "synthetic",
                tracking,
                "https://example.invalid/labels/" + encodedShipment + "/" + encodedRate + ".pdf");
    }

    private Address toAddress(ShippingFixture.AddressFixture fixtureAddress) {
        var ep = EasyPostAddress.newBuilder()
                .setId(defaultString(fixtureAddress.id()))
                .setCompany(defaultString(fixtureAddress.company()))
                .setStreet1(defaultString(fixtureAddress.street1()))
                .setStreet2(defaultString(fixtureAddress.street2()))
                .setCity(defaultString(fixtureAddress.city()))
                .setState(defaultString(fixtureAddress.state()))
                .setZip(defaultString(fixtureAddress.zip()))
                .setCountry(defaultCountry(fixtureAddress.country()))
                .setTimezone(defaultString(fixtureAddress.timezone()));

        if (fixtureAddress.residential() != null) {
            ep.setResidential(fixtureAddress.residential());
        }
        if (fixtureAddress.coordinate() != null) {
            ep.setCoordinate(Coordinate.newBuilder()
                    .setLatitude(defaultDouble(fixtureAddress.coordinate().latitude(), 0.0))
                    .setLongitude(defaultDouble(fixtureAddress.coordinate().longitude(), 0.0))
                    .build());
        }

        return Address.newBuilder().setEasypost(ep).build();
    }

    private Money toMoney(ShippingFixture.MoneyFixture money) {
        return Money.newBuilder()
                .setCurrency(money == null || money.currency() == null ? "USD" : money.currency())
                .setUnits(defaultLong(money == null ? null : money.units(), 0L))
                .build();
    }

    private static boolean handlesSku(ShippingFixture.WarehouseFixture warehouse, String skuId) {
        if (warehouse.skuPrefixes().isEmpty()) {
            return true;
        }
        return warehouse.skuPrefixes().stream().anyMatch(skuId::startsWith);
    }

    private static ShippingFixture loadFixture(
            String fixturePath,
            ResourceLoader resourceLoader,
            ObjectMapper objectMapper) {
        Resource resource = resourceLoader.getResource(fixturePath);
        if (!resource.exists()) {
            throw new IllegalStateException("Shipping fixture does not exist: " + fixturePath);
        }
        try (InputStream input = resource.getInputStream()) {
            return objectMapper.readValue(input, ShippingFixture.class);
        } catch (IOException e) {
            throw new IllegalStateException("Failed to load shipping fixture: " + fixturePath, e);
        }
    }

    private static Map<String, ShippingFixture.AddressFixture> indexAddressesById(ShippingFixture fixture) {
        Map<String, ShippingFixture.AddressFixture> result = new LinkedHashMap<>();
        for (var address : fixture.addresses()) {
            result.put(address.id(), address);
        }
        return Map.copyOf(result);
    }

    private static Map<String, ShippingFixture.AddressFixture> indexAddressesByKey(ShippingFixture fixture) {
        Map<String, ShippingFixture.AddressFixture> result = new HashMap<>();
        for (var address : fixture.addresses()) {
            result.put(addressKey(address.street1(), address.street2(), address.city(), address.state(), address.zip(), address.country()), address);
        }
        return Map.copyOf(result);
    }

    private static Map<String, ShippingFixture.ShipmentFixture> indexShipmentsById(ShippingFixture fixture) {
        Map<String, ShippingFixture.ShipmentFixture> result = new LinkedHashMap<>();
        for (var shipment : fixture.shipments()) {
            result.put(shipment.shipmentId(), sortedRates(shipment));
        }
        return Map.copyOf(result);
    }

    private static Map<String, ShippingFixture.ShipmentFixture> indexShipmentsByPair(ShippingFixture fixture) {
        Map<String, ShippingFixture.ShipmentFixture> result = new LinkedHashMap<>();
        for (var shipment : fixture.shipments()) {
            result.put(pairKey(shipment.fromAddressId(), shipment.toAddressId()), sortedRates(shipment));
        }
        return Map.copyOf(result);
    }

    private static ShippingFixture.ShipmentFixture sortedRates(ShippingFixture.ShipmentFixture shipment) {
        var sorted = shipment.rates().stream()
                .sorted(Comparator.comparingInt(rate -> defaultInt(rate.estimatedDays(), Integer.MAX_VALUE)))
                .toList();
        return new ShippingFixture.ShipmentFixture(
                shipment.shipmentId(),
                shipment.fromAddressId(),
                shipment.toAddressId(),
                shipment.parcel(),
                sorted,
                shipment.labels());
    }

    private static String pairKey(String fromAddressId, String toAddressId) {
        return fromAddressId + "->" + toAddressId;
    }

    private static String addressKey(String street1, String street2, String city, String state, String zip, String country) {
        return normalize(street1)
                + "|" + normalize(street2)
                + "|" + normalize(city)
                + "|" + normalize(state)
                + "|" + normalize(zip)
                + "|" + normalize(defaultCountry(country));
    }

    private static String addressDescription(EasyPostAddress address) {
        if (!address.getId().isBlank()) {
            return "id=" + address.getId();
        }
        return address.getStreet1() + ", " + address.getCity() + ", " + address.getState() + " " + address.getZip();
    }

    private static String shipmentNotFoundMessage(GetShippingRatesRequest request) {
        if (request.hasSelectedShipment()
                && request.getSelectedShipment().hasEasypost()
                && !request.getSelectedShipment().getEasypost().getShipmentId().isBlank()
                && (request.getFromEasypostId().isBlank() || request.getToEasypostId().isBlank())) {
            return "No fixture shipment for " + request.getSelectedShipment().getEasypost().getShipmentId();
        }
        return "No fixture shipment for " + request.getFromEasypostId() + " -> " + request.getToEasypostId();
    }

    private static String normalize(String value) {
        return defaultString(value).trim().replaceAll("\\s+", " ").toUpperCase(Locale.ROOT);
    }

    private static String defaultString(String value) {
        return value == null ? "" : value;
    }

    private static String defaultCountry(String country) {
        return country == null || country.isBlank() ? "US" : country;
    }

    private static int defaultInt(Integer value, int fallback) {
        return value == null ? fallback : value;
    }

    private static long defaultLong(Long value, long fallback) {
        return value == null ? fallback : value;
    }

    private static double defaultDouble(Double value, double fallback) {
        return value == null ? fallback : value;
    }

    private static String sha256Hex(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder result = new StringBuilder(hash.length * 2);
            for (byte b : hash) {
                result.append(String.format("%02x", b));
            }
            return result.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 is not available", e);
        }
    }
}
