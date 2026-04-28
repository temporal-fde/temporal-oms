from __future__ import annotations

from temporalio import activity

from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    GetLocationEventsRequest,
    GetLocationEventsResponse,
)
from acme.fulfillment.domain.v1.values_p2p import (
    LocationRiskSummary,
    RiskLevel,
)


class LocationEventsActivities:

    @activity.defn
    async def get_location_events(
        self,
        request: GetLocationEventsRequest,
    ) -> GetLocationEventsResponse:
        activity.logger.info(
            "get_location_events (stubbed) — returning no events for %.4f,%.4f",
            request.coordinate.latitude,
            request.coordinate.longitude,
        )
        return GetLocationEventsResponse(
            summary=LocationRiskSummary(
                overall_risk_level=RiskLevel.RISK_LEVEL_NONE,
                peak_rank=0,
                total_event_count=0,
                unscheduled_event_count=0,
                events_by_category={},
            ),
            events=[],
            window_from=request.active_from,
            window_to=request.active_to,
            timezone=request.timezone,
        )
