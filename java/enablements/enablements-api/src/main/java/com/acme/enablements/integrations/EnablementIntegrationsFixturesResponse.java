package com.acme.enablements.integrations;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record EnablementIntegrationsFixturesResponse(
        List<ShippingFixture.WarehouseFixture> warehouses,
        @JsonProperty("shipping_addresses") List<ShippingFixture.AddressFixture> shippingAddresses,
        @JsonProperty("shipping_shipments") List<ShipmentState> shippingShipments,
        @JsonProperty("location_events") ShippingFixture.LocationEventsFixture locationEvents
) {
    public record ShipmentState(
            @JsonProperty("shipment_id") String shipmentId,
            @JsonProperty("from_address_id") String fromAddressId,
            @JsonProperty("to_address_id") String toAddressId,
            ShippingFixture.ParcelFixture parcel,
            List<ShippingFixture.RateFixture> rates,
            List<ShippingFixture.LabelFixture> labels
    ) {
    }
}
