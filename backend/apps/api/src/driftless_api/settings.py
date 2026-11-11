from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr

from driftless_core.config import DriftlessSettings


class ApiSettings(DriftlessSettings):
    service_name: str = "driftless-api"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    host: str = "0.0.0.0"  # noqa: S104 - container default; restrict via network policy
    port: int = 8000

    # Metadata database. Unset = in-memory store (local dev only; refused in production).
    database_url: str | None = None

    # Secret backends. `env:` is for local dev/CI; enable Vault in real deployments.
    secret_env_enabled: bool = True
    vault_addr: str | None = None
    vault_token: SecretStr | None = None
    vault_mount: str = "secret"
    vault_namespace: str | None = None


@lru_cache
def get_settings() -> ApiSettings:
    return ApiSettings()
