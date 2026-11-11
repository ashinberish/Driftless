from __future__ import annotations

from driftless_core.config import DriftlessSettings


class WorkerSettings(DriftlessSettings):
    service_name: str = "driftless-worker"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    task_queue: str = "driftless-migrations"
