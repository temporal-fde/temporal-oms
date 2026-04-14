from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timezone

import aiohttp
from temporalio import activity
from temporalio.exceptions import ApplicationError

from acme.fulfillments.domain.v1.shipping_agent_p2p import (
    GetLocationEventsRequest,
    GetLocationEventsResponse,
)
from acme.fulfillments.domain.v1.values_p2p import (
    Errors,
    LocationEvent,
    LocationRiskSummary,
    RiskLevel,
)

# TODO All these global settings will be injected via a config
_PREDICTHQ_BASE_URL = "https://api.predicthq.com/v1"

# TODO All these global settings will be injected via a config
_UNSCHEDULED_CATEGORIES: frozenset[str] = frozenset({
    "severe-weather",
    "disasters",
    "terror",
    "health-warnings",
    "airport-delays",
})


def _rank_to_risk_level(rank: int) -> RiskLevel:
    if rank == 0:
        return RiskLevel.RISK_LEVEL_NONE
    if rank <= 30:
        return RiskLevel.RISK_LEVEL_LOW
    if rank <= 60:
        return RiskLevel.RISK_LEVEL_MODERATE
    if rank <= 80:
        return RiskLevel.RISK_LEVEL_HIGH
    return RiskLevel.RISK_LEVEL_CRITICAL


def _to_iso_date(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _parse_datetime(iso_str: str | None) -> datetime | None:
    if not iso_str:
        return None
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))


class LocationEventsActivities:
    """Temporal activity class for fetching location-based event risk data
    from the PredictHQ Events API.

    Uses raw aiohttp rather than the predicthq Python SDK. The SDK is
    synchronous (requests-based) and provides no mechanism for injecting
    an async transport. Wrapping it in asyncio.to_thread would work but
    consumes a thread per concurrent activity invocation — a poor fit for
    a Temporal worker running many agent tool calls concurrently. aiohttp
    gives true async I/O with no thread overhead.

    Inject an aiohttp.ClientSession at construction time so the session
    lifecycle (connection pooling, SSL context) is owned by the worker,
    not re-created per activity execution.
    """

    def __init__(self, http_client: aiohttp.ClientSession) -> None:
        self._http_client = http_client

    ## TODO: Worker rate limits this PredictHQ usage to 50 task queue activities per second
    ## https://docs.predicthq.com/api/overview/rate-limits
    @activity.defn
    async def get_location_events(
        self,
        request: GetLocationEventsRequest,
    ) -> GetLocationEventsResponse:
        """Queries PredictHQ for unscheduled events near the destination
        that overlap the ship-to-delivery window.

        Returns a risk summary and event list for the ShippingAgent LLM
        to reason about — no shipping logic here.
        """
        params = {
            "within": (
                f"{request.within_km}km"
                f"@{request.coordinate.latitude},{request.coordinate.longitude}"
            ),
            "active.gte": _to_iso_date(request.active_from),
            "active.lte": _to_iso_date(request.active_to),
            "active.tz": request.timezone,
            "category": ",".join(_UNSCHEDULED_CATEGORIES),
            "sort": "-rank",
            "limit": "20",
        }

        headers = {
            "Authorization": f"Bearer {os.getenv('PREDICTHQ_API_KEY', '')}",
            "Accept": "application/json",
        }

        activity.logger.info(
            "Fetching PredictHQ events within=%.1fkm@%.4f,%.4f active=%s/%s",
            request.within_km,
            request.coordinate.latitude,
            request.coordinate.longitude,
            params["active.gte"],
            params["active.lte"],
        )

        info = activity.info()
        timeout = aiohttp.ClientTimeout(total=info.start_to_close_timeout.total_seconds() - 1.0)

        async with self._http_client.get(
            f"{_PREDICTHQ_BASE_URL}/events/",
            params=params,
            headers=headers,
            timeout=timeout,
        ) as resp:
            if resp.status == 401:
                raise ApplicationError(
                    "PredictHQ API: unauthorized — check PREDICTHQ_API_KEY",
                    type=Errors.ERROR_UNAUTHORIZED.name,
                    non_retryable=True,
                )
            if resp.status == 403:
                raise ApplicationError(
                    "PredictHQ API: forbidden — token lacks required scope",
                    type=Errors.ERROR_FORBIDDEN.name,
                    non_retryable=True,
                )
            resp.raise_for_status()
            body = await resp.json()

        return _build_response(request, body)


def _build_response(
    request: GetLocationEventsRequest,
    body: dict,
) -> GetLocationEventsResponse:
    events: list[LocationEvent] = []
    events_by_category: dict[str, int] = defaultdict(int)
    peak_rank = 0

    for raw in body.get("results", []):
        category: str = raw.get("category", "")
        rank: int = raw.get("rank", 0)

        events_by_category[category] += 1
        if rank > peak_rank:
            peak_rank = rank

        events.append(LocationEvent(
            id=raw["id"],
            title=raw.get("title", ""),
            category=category,
            rank=rank,
            unscheduled=category in _UNSCHEDULED_CATEGORIES,
            description=raw.get("description"),
            local_rank=raw.get("local_rank"),
            start=_parse_datetime(raw.get("start")) or datetime.now(tz=timezone.utc),
            end=_parse_datetime(raw.get("end")),
        ))

    unscheduled_count = sum(
        n for cat, n in events_by_category.items()
        if cat in _UNSCHEDULED_CATEGORIES
    )

    return GetLocationEventsResponse(
        summary=LocationRiskSummary(
            overall_risk_level=_rank_to_risk_level(peak_rank),
            peak_rank=peak_rank,
            total_event_count=len(events),
            unscheduled_event_count=unscheduled_count,
            events_by_category=dict(events_by_category),
        ),
        events=events,
        window_from=request.active_from,
        window_to=request.active_to,
        timezone=request.timezone,
    )
