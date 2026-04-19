from __future__ import annotations

import os

import aiohttp
from temporalio.client import Client
from temporalio.worker import Worker

from src.agents.activities.location_events import LocationEventsActivities

_TASK_QUEUE = "fulfillment-predicthq"
_NAMESPACE = "fulfillment"


async def build_predicthq_worker() -> Worker:
    client = await Client.connect(
        os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
        namespace=_NAMESPACE,
    )
    http_client = aiohttp.ClientSession()
    location_activities = LocationEventsActivities(http_client=http_client)
    return Worker(
        client,
        task_queue=_TASK_QUEUE,
        activities=[location_activities.get_location_events],
        max_activities_per_second=50.0,
    )
