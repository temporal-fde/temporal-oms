from __future__ import annotations

import aiohttp
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from src.config import settings
from src.agents.activities.location_events import LocationEventsActivities

_TASK_QUEUE = "fulfillment-predicthq"


async def build_predicthq_worker() -> Worker:
    client = await Client.connect(
        settings.temporal_fulfillment_address,
        namespace=settings.temporal_fulfillment_namespace,
        api_key=settings.temporal_fulfillment_api_key or None,
        data_converter=pydantic_data_converter,
    )
    http_client = aiohttp.ClientSession()
    location_activities = LocationEventsActivities(http_client=http_client)
    return Worker(
        client,
        task_queue=_TASK_QUEUE,
        activities=[location_activities.get_location_events],
        max_activities_per_second=50.0,
    )
