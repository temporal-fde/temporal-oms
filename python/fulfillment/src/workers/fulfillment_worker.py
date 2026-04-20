from __future__ import annotations

import os

from temporalio.client import Client
from temporalio.worker import Worker

from src.agents.activities.inventory import LookupInventoryActivities
from src.agents.activities.llm import LlmActivities
from src.agents.workflows.shipping_agent import ShippingAgent

_TASK_QUEUE = "fulfillment"
_NAMESPACE = "fulfillment"


async def build_fulfillment_worker() -> Worker:
    client = await Client.connect(
        os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
        namespace=_NAMESPACE,
    )
    inventory_activities = LookupInventoryActivities()
    llm_activities = LlmActivities()
    return Worker(
        client,
        task_queue=_TASK_QUEUE,
        workflows=[ShippingAgent],
        activities=[
            inventory_activities.lookup_inventory_location,
            llm_activities.build_system_prompt,
            llm_activities.call_llm,
        ],
    )
