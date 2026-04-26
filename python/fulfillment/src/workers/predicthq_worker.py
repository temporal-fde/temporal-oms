from __future__ import annotations

import logging

import aiohttp
from temporalio.client import Client
from src.converter import proto_pydantic_data_converter
from temporalio.worker import Worker

from src.config import settings
from src.agents.activities.location_events import LocationEventsActivities

_TASK_QUEUE = "fulfillment-predicthq"
_log = logging.getLogger(__name__)


async def build_predicthq_worker() -> Worker:
    client = await Client.connect(
        settings.temporal_fulfillment_address,
        namespace=settings.temporal_fulfillment_namespace,
        api_key=settings.temporal_fulfillment_api_key or None,
        data_converter=proto_pydantic_data_converter,
    )
    _log.info("[%s] connected — activities: get_location_events (max 50 rps)", _TASK_QUEUE)
    http_client = aiohttp.ClientSession()
    location_activities = LocationEventsActivities(http_client=http_client)
    return Worker(
        client,
        task_queue=_TASK_QUEUE,
        activities=[location_activities.get_location_events],
        max_activities_per_second=50.0,
    )
