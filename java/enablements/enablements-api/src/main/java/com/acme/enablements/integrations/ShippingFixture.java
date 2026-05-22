package com.acme.enablements.integrations;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record ShippingFixture(
        List<AddressFixture> addresses,
        List<WarehouseFixture> warehouses,
        List<ShipmentFixture> shipments,
        @JsonProperty("location_events") LocationEventsFixture locationEvents
) {
    public ShippingFixture {
        addresses = addresses == null ? List.of() : List.copyOf(addresses);
        warehouses = warehouses == null ? List.of() : List.copyOf(warehouses);
        shipments = shipments == null ? List.of() : List.copyOf(shipments);
        locationEvents = locationEvents == null
                ? new LocationEventsFixture("empty", List.of())
                : locationEvents;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record AddressFixture(
            String id,
            String company,
            String street1,
            String street2,
            String city,
            String state,
            String zip,
            String country,
            Boolean residential,
            CoordinateFixture coordinate,
            String timezone
    ) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record WarehouseFixture(
            @JsonProperty("warehouse_id") String warehouseId,
            @JsonProperty("address_id") String addressId,
            @JsonProperty("sku_prefixes") List<String> skuPrefixes
    ) {
        public WarehouseFixture {
            skuPrefixes = skuPrefixes == null ? List.of() : List.copyOf(skuPrefixes);
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record ShipmentFixture(
            @JsonProperty("shipment_id") String shipmentId,
            @JsonProperty("from_address_id") String fromAddressId,
            @JsonProperty("to_address_id") String toAddressId,
            ParcelFixture parcel,
            List<RateFixture> rates,
            List<LabelFixture> labels
    ) {
        public ShipmentFixture {
            rates = rates == null ? List.of() : List.copyOf(rates);
            labels = labels == null ? List.of() : List.copyOf(labels);
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record RateFixture(
            @JsonProperty("rate_id") String rateId,
            String carrier,
            @JsonProperty("service_level") String serviceLevel,
            MoneyFixture cost,
            @JsonProperty("estimated_days") Integer estimatedDays,
            @JsonProperty("delivery_days") Integer deliveryDays
    ) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record LabelFixture(
            @JsonProperty("rate_id") String rateId,
            String source,
            @JsonProperty("tracking_number") String trackingNumber,
            @JsonProperty("label_url") String labelUrl
    ) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record MoneyFixture(String currency, Long units) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record CoordinateFixture(Double latitude, Double longitude) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record ParcelFixture(
            @JsonProperty("weight_oz") Double weightOz,
            @JsonProperty("length_in") Double lengthIn,
            @JsonProperty("width_in") Double widthIn,
            @JsonProperty("height_in") Double heightIn
    ) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record LocationEventsFixture(String mode, List<String> seeds) {
        public LocationEventsFixture {
            seeds = seeds == null ? List.of() : List.copyOf(seeds);
        }
    }
}
