"""Worker entry point: connect to Temporal and serve workflows + activities."""

from __future__ import annotations

import asyncio

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from driftless_core.logging import configure_logging, get_logger
from driftless_worker.activities import ALL_ACTIVITIES
from driftless_worker.settings import WorkerSettings
from driftless_worker.workflows import ALL_WORKFLOWS


async def serve(settings: WorkerSettings) -> None:
    log = get_logger("worker")
    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        data_converter=pydantic_data_converter,
    )
    worker = Worker(
        client,
        task_queue=settings.task_queue,
        workflows=ALL_WORKFLOWS,
        activities=ALL_ACTIVITIES,
    )
    log.info("worker.started", task_queue=settings.task_queue, address=settings.temporal_address)
    await worker.run()


def run() -> None:
    settings = WorkerSettings()
    configure_logging(
        level=settings.log_level, json=settings.log_json, service=settings.service_name
    )
    asyncio.run(serve(settings))
