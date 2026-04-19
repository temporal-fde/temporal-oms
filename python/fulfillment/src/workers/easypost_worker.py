from __future__ import annotations

import os

from temporalio.client import Client
from temporalio.worker import Worker

from src.agents.activities.easypost import EasyPostActivities

_TASK_QUEUE = "fulfillment-easypost"
_NAMESPACE = "fulfillment"


async def build_easypost_worker() -> Worker:
    client = await Client.connect(
        os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
        namespace=_NAMESPACE,
    )
    easypost_activities = EasyPostActivities()
    return Worker(
        client,
        task_queue=_TASK_QUEUE,
        activities=[
            easypost_activities.verify_address,
            easypost_activities.get_carrier_rates,
        ],
        max_activities_per_second=5.0,
    )
