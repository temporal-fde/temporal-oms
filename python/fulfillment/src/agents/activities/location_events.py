from __future__ import annotations

import asyncio

from temporalio import activity

from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    GetLocationEventsRequest,
    GetLocationEventsResponse,
)
from temporalio.exceptions import ApplicationError

from src.services.enablements_integrations import (
    EnablementsIntegrationError,
    EnablementsIntegrationsClient,
)


class LocationEventsActivities:

    def __init__(self, client: EnablementsIntegrationsClient | None = None) -> None:
        self._client = client or EnablementsIntegrationsClient()

    @activity.defn
    async def get_location_events(
        self,
        request: GetLocationEventsRequest,
    ) -> GetLocationEventsResponse:
        activity.logger.info(
            "get_location_events via enablements-api for %.4f,%.4f",
            request.coordinate.latitude,
            request.coordinate.longitude,
        )
        try:
            return await asyncio.to_thread(self._client.get_location_events, request)
        except EnablementsIntegrationError as e:
            raise ApplicationError(str(e), type=e.code, non_retryable=e.status < 500) from e
