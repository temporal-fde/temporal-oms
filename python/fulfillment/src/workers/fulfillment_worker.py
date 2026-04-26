from __future__ import annotations

import logging

from temporalio.client import Client
from temporalio.worker import Worker

from src.config import settings
from src.converter import proto_pydantic_data_converter
from src.agents.activities.llm import LlmActivities
from src.agents.workflows.shipping_agent import ShippingAgent
from src.services.shipping_agent_impl import ShippingAgentImpl


_TASK_QUEUE = "agents"
_log = logging.getLogger(__name__)


async def build_fulfillment_worker() -> Worker:
    client = await Client.connect(
        settings.temporal_fulfillment_address,
        namespace=settings.temporal_fulfillment_namespace,
        api_key=settings.temporal_fulfillment_api_key or None,
        data_converter=proto_pydantic_data_converter,
    )
    _log.info("[%s] connected — workflows: ShippingAgent | activities: build_system_prompt, call_llm | nexus: ShippingAgent", _TASK_QUEUE)
    llm_activities = LlmActivities()
    return Worker(
        client,
        task_queue=_TASK_QUEUE,
        workflows=[ShippingAgent],
        activities=[
            llm_activities.build_system_prompt,
            llm_activities.call_llm,
        ],
        nexus_service_handlers=[ShippingAgentImpl()],
    )
