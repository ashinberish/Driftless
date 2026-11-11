from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from driftless_core.config import DriftlessSettings


class ApiSettings(DriftlessSettings):
    service_name: str = "driftless-api"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    host: str = "0.0.0.0"  # noqa: S104 - container default; restrict via network policy
    port: int = 8000


@lru_cache
def get_settings() -> ApiSettings:
    return ApiSettings()
