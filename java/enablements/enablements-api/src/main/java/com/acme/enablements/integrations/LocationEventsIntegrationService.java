package com.acme.enablements.integrations;

import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetLocationEventsRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetLocationEventsResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LocationRiskSummary;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.RiskLevel;
import org.springframework.stereotype.Service;

@Service
public class LocationEventsIntegrationService {

    private final ShippingFixtureService shipping;

    public LocationEventsIntegrationService(ShippingFixtureService shipping) {
        this.shipping = shipping;
    }

    public ShippingFixture.LocationEventsFixture fixtureConfig() {
        return shipping.locationEventsFixture();
    }

    public GetLocationEventsResponse getLocationEvents(GetLocationEventsRequest request) {
        return GetLocationEventsResponse.newBuilder()
                .setSummary(LocationRiskSummary.newBuilder()
                        .setOverallRiskLevel(RiskLevel.RISK_LEVEL_NONE)
                        .setPeakRank(0)
                        .setTotalEventCount(0)
                        .setUnscheduledEventCount(0)
                        .build())
                .setWindowFrom(request.getActiveFrom())
                .setWindowTo(request.getActiveTo())
                .setTimezone(request.getTimezone())
                .build();
    }
}
