"""Base settings shared by all services.

Each app subclasses :class:`DriftlessSettings` and adds its own fields. Values come from
environment variables prefixed with ``DRIFTLESS_`` (and an optional ``.env`` file).
Secrets are never stored here — only references (e.g. a Vault path).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class DriftlessSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DRIFTLESS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Environment.LOCAL
    log_level: str = "INFO"
    log_json: bool = False
    service_name: str = "driftless"

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION
