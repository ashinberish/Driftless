"""Secret backends available to the API and how they are assembled from settings."""

from __future__ import annotations

import httpx
from pydantic import SecretStr

from driftless_api.settings import ApiSettings
from driftless_core.errors import ConfigurationError
from driftless_core.secrets import EnvSecretResolver, SecretNotFoundError, SecretResolverRegistry


class VaultSecretResolver:
    """``vault:<path>[#field]`` — HashiCorp Vault KV v2. ``field`` defaults to ``password``."""

    scheme = "vault"

    def __init__(
        self,
        addr: str,
        token: SecretStr,
        *,
        mount: str = "secret",
        namespace: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._addr = addr.rstrip("/")
        self._token = token
        self._mount = mount.strip("/")
        self._namespace = namespace
        self._transport = transport

    async def resolve(self, path: str) -> SecretStr:
        secret_path, _, field = path.partition("#")
        field = field or "password"
        headers = {"X-Vault-Token": self._token.get_secret_value()}
        if self._namespace:
            headers["X-Vault-Namespace"] = self._namespace
        url = f"{self._addr}/v1/{self._mount}/data/{secret_path.strip('/')}"
        async with httpx.AsyncClient(transport=self._transport, timeout=10) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.HTTPError as exc:
                raise ConfigurationError(f"cannot reach Vault: {exc}") from exc
        reference = {"reference": f"vault:{path}"}
        if response.status_code == 404:
            raise SecretNotFoundError(f"Vault secret {secret_path!r} not found", details=reference)
        if response.status_code in (401, 403):
            raise ConfigurationError("Vault denied access to the secret", details=reference)
        response.raise_for_status()
        data: dict[str, object] = response.json().get("data", {}).get("data", {})
        value = data.get(field)
        if not isinstance(value, str):
            raise SecretNotFoundError(
                f"Vault secret {secret_path!r} has no field {field!r}", details=reference
            )
        return SecretStr(value)


def build_secret_registry(settings: ApiSettings) -> SecretResolverRegistry:
    registry = SecretResolverRegistry()
    if settings.secret_env_enabled:
        registry.register(EnvSecretResolver())
    if settings.vault_addr:
        if settings.vault_token is None:
            raise ConfigurationError("DRIFTLESS_VAULT_TOKEN is required when VAULT_ADDR is set")
        registry.register(
            VaultSecretResolver(
                settings.vault_addr,
                settings.vault_token,
                mount=settings.vault_mount,
                namespace=settings.vault_namespace,
            )
        )
    return registry
