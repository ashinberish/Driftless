from collections.abc import Sequence
from typing import ClassVar

import pytest

from driftless_connectors import registry
from driftless_connectors.postgres import PostgresConnector, PostgresTypeMapper
from driftless_connectors.sdk import (
    Capabilities,
    ConnectionCheck,
    ConnectionConfig,
    Connector,
    ConnectorRegistry,
    TypeMapper,
)
from driftless_core.errors import NotFoundError, UnsupportedFeatureError
from driftless_core.schema import Catalog


def _config(engine: str = "postgres") -> ConnectionConfig:
    return ConnectionConfig(
        engine=engine, host="localhost", port=5432, database="app", username="u"
    )


def test_builtin_connectors_are_registered() -> None:
    assert {"postgres", "mysql"} <= set(registry.engines())
    assert isinstance(registry.create(_config()), PostgresConnector)


def test_unknown_engine_raises_not_found_with_available_list() -> None:
    with pytest.raises(NotFoundError) as info:
        registry.get("db2")
    assert "postgres" in info.value.details["available"]


def test_entry_points_load_without_conflict() -> None:
    fresh = ConnectorRegistry()
    fresh.load_plugins()
    assert {"postgres", "mysql"} <= set(fresh.engines())


def test_duplicate_engine_registration_rejected() -> None:
    fresh = ConnectorRegistry()
    fresh.register(PostgresConnector)

    class Impostor(PostgresConnector):
        pass

    with pytest.raises(ValueError, match="already registered"):
        fresh.register(Impostor)


def test_connector_rejects_config_for_other_engine() -> None:
    with pytest.raises(ValueError, match="cannot use"):
        PostgresConnector(_config("mysql"))


async def test_unsupported_operations_raise_clear_error() -> None:
    class Minimal(Connector):
        engine: ClassVar[str] = "minimal"
        display_name: ClassVar[str] = "Minimal"
        dialect: ClassVar[str] = "postgres"
        default_port: ClassVar[int] = 1
        capabilities: ClassVar[Capabilities] = Capabilities()
        type_mapper: ClassVar[TypeMapper] = PostgresTypeMapper()

        async def check(self) -> Sequence[ConnectionCheck]:
            return []

        async def discover(self, schemas: Sequence[str] | None = None) -> Catalog:
            return Catalog(engine=self.engine)

    conn = Minimal(_config("minimal"))
    async with conn:
        assert (await conn.discover()).engine == "minimal"
        with pytest.raises(UnsupportedFeatureError, match="change data capture"):
            conn.stream_changes(since=None)  # type: ignore[arg-type]
