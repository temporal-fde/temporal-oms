from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from src.converter import proto_pydantic_data_converter
from temporalio.worker import Worker

from src.config import settings
from src.agents.activities.easypost import EasyPostActivities

_TASK_QUEUE = "fulfillment-easypost"
_log = logging.getLogger(__name__)


async def build_easypost_worker() -> Worker:
    client = await Client.connect(
        settings.temporal_fulfillment_address,
        namespace=settings.temporal_fulfillment_namespace,
        api_key=settings.temporal_fulfillment_api_key or None,
        data_converter=proto_pydantic_data_converter,
    )
    _log.info("[%s] connected — activities: verify_address, get_carrier_rates (max 5 rps)", _TASK_QUEUE)
    easypost_activities = EasyPostActivities()
    return Worker(
        client,
        task_queue=_TASK_QUEUE,
        activities=[
            easypost_activities.verify_address,
            easypost_activities.get_carrier_rates,
        ],
        activity_executor=ThreadPoolExecutor(max_workers=10),
        max_activities_per_second=5.0,
    )
