from __future__ import annotations

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from src.config import settings
from src.agents.activities.inventory import LookupInventoryActivities
from src.agents.activities.llm import LlmActivities
from src.agents.workflows.shipping_agent import ShippingAgent

_TASK_QUEUE = "fulfillment"


async def build_fulfillment_worker() -> Worker:
    client = await Client.connect(
        settings.temporal_fulfillment_address,
        namespace=settings.temporal_fulfillment_namespace,
        api_key=settings.temporal_fulfillment_api_key or None,
        data_converter=pydantic_data_converter,
    )
    inventory_activities = LookupInventoryActivities()
    llm_activities = LlmActivities()
    return Worker(
        client,
        task_queue=_TASK_QUEUE,
        workflows=[ShippingAgent],
        activities=[
            inventory_activities.lookup_inventory_address,
            inventory_activities.find_alternate_warehouse,
            llm_activities.build_system_prompt,
            llm_activities.call_llm,
        ],
    )
