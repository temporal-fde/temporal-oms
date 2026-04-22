"""Entry point for python -m src.worker (as invoked by the Dockerfile).

Starts all three Temporal workers in a single process concurrently:
  - fulfillment       (ShippingAgent workflow + LookupInventory + LLM activities)
  - fulfillment-easypost  (EasyPost activities, 5 rps)
  - fulfillment-predicthq (PredictHQ activities, 50 rps)
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

from src.workers.easypost_worker import build_easypost_worker
from src.workers.fulfillment_worker import build_fulfillment_worker
from src.workers.predicthq_worker import build_predicthq_worker


async def main() -> None:
    fulfillment, easypost, predicthq = await asyncio.gather(
        build_fulfillment_worker(),
        build_easypost_worker(),
        build_predicthq_worker(),
    )

    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def _handle_sigterm(*_: object) -> None:
        shutdown_event.set()

    loop.add_signal_handler(signal.SIGTERM, _handle_sigterm)
    loop.add_signal_handler(signal.SIGINT, _handle_sigterm)

    async with fulfillment, easypost, predicthq:
        await shutdown_event.wait()


if __name__ == "__main__":
    asyncio.run(main())
