import pytest

from driftless_core.errors import ConfigurationError
from driftless_core.secrets import (
    EnvSecretResolver,
    SecretNotFoundError,
    SecretRef,
    SecretResolver,
    SecretResolverRegistry,
)


def test_parse_reference() -> None:
    ref = SecretRef.parse("vault:db/billing-ro")
    assert (ref.scheme, ref.path) == ("vault", "db/billing-ro")
    assert str(ref) == "vault:db/billing-ro"


@pytest.mark.parametrize("bad", ["", "hunter2", ":path", "Vault:x", "env:"])
def test_parse_rejects_plain_values(bad: str) -> None:
    with pytest.raises(ValueError, match="not a secret reference"):
        SecretRef.parse(bad)


async def test_env_resolver_reads_value_without_exposing_it() -> None:
    resolver = EnvSecretResolver({"DB_PW": "s3cret"})
    assert isinstance(resolver, SecretResolver)
    value = await resolver.resolve("DB_PW")
    assert value.get_secret_value() == "s3cret"
    assert "s3cret" not in repr(value)


async def test_env_resolver_missing_variable() -> None:
    with pytest.raises(SecretNotFoundError):
        await EnvSecretResolver({}).resolve("MISSING")


async def test_registry_routes_by_scheme() -> None:
    registry = SecretResolverRegistry([EnvSecretResolver({"PW": "x"})])
    assert registry.schemes == ["env"]
    assert registry.supports("env:PW")
    assert not registry.supports("vault:db/x")
    assert (await registry.resolve("env:PW")).get_secret_value() == "x"
    with pytest.raises(ConfigurationError) as info:
        await registry.resolve("vault:db/x")
    assert info.value.details["available"] == ["env"]
