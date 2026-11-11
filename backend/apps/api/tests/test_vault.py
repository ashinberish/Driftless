import httpx
import pytest
from pydantic import SecretStr

from driftless_api.platform.secrets import VaultSecretResolver, build_secret_registry
from driftless_api.settings import ApiSettings
from driftless_core.errors import ConfigurationError
from driftless_core.secrets import SecretNotFoundError


def _vault(handler: httpx.MockTransport) -> VaultSecretResolver:
    return VaultSecretResolver(
        "https://vault.internal", SecretStr("tok"), namespace="team-a", transport=handler
    )


async def test_reads_kv2_password_field() -> None:
    def handle(req: httpx.Request) -> httpx.Response:
        assert req.url.path == "/v1/secret/data/db/billing-ro"
        assert req.headers["X-Vault-Token"] == "tok"
        assert req.headers["X-Vault-Namespace"] == "team-a"
        return httpx.Response(200, json={"data": {"data": {"password": "pw", "user": "u"}}})

    resolver = _vault(httpx.MockTransport(handle))
    assert (await resolver.resolve("db/billing-ro")).get_secret_value() == "pw"


async def test_custom_field() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, json={"data": {"data": {"pg_pass": "x"}}})
    )
    assert (await _vault(transport).resolve("db/a#pg_pass")).get_secret_value() == "x"


@pytest.mark.parametrize(
    ("status", "error"), [(404, SecretNotFoundError), (403, ConfigurationError)]
)
async def test_error_statuses(status: int, error: type[Exception]) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(status, json={}))
    with pytest.raises(error):
        await _vault(transport).resolve("db/missing")


def test_registry_from_settings() -> None:
    assert build_secret_registry(ApiSettings()).schemes == ["env"]
    with_vault = ApiSettings(vault_addr="https://v", vault_token=SecretStr("t"))
    assert build_secret_registry(with_vault).schemes == ["env", "vault"]
    prod = ApiSettings(secret_env_enabled=False, vault_addr="https://v", vault_token=SecretStr("t"))
    assert build_secret_registry(prod).schemes == ["vault"]
    with pytest.raises(ConfigurationError):
        build_secret_registry(ApiSettings(vault_addr="https://v"))
