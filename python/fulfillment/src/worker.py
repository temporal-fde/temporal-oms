"""Entry point for python -m src.worker (as invoked by the Dockerfile).

Starts two Temporal workers in a single process concurrently:
  - agents               (ShippingAgent workflow + LLM + location events activities + ShippingAgent Nexus service)
  - fulfillment-shipping  (fixture-backed shipping activities)
"""
from __future__ import annotations

import asyncio
import logging
import signal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

from src.config import settings
from src.workers.fulfillment_worker import build_fulfillment_worker
from src.workers.shipping_worker import build_shipping_worker

_log = logging.getLogger(__name__)


async def main() -> None:
    _log.info("Connecting to Temporal at %s (namespace: %s)", settings.temporal_fulfillment_address, settings.temporal_fulfillment_namespace)

    fulfillment, shipping = await asyncio.gather(
        build_fulfillment_worker(),
        build_shipping_worker(),
    )

    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def _handle_sigterm(*_: object) -> None:
        shutdown_event.set()

    loop.add_signal_handler(signal.SIGTERM, _handle_sigterm)
    loop.add_signal_handler(signal.SIGINT, _handle_sigterm)

    async with fulfillment, shipping:
        _log.info("All workers polling — press Ctrl+C to stop")
        await shutdown_event.wait()


if __name__ == "__main__":
    asyncio.run(main())
