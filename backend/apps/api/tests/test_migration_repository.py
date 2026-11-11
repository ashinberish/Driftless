"""Contract tests: every MigrationRepository implementation must behave the same."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from driftless_api.modules.connections.repository import (
    ConnectionRepository,
    InMemoryConnectionRepository,
    SqlConnectionRepository,
)
from driftless_api.modules.connections.schemas import Connection
from driftless_api.modules.migrations.repository import (
    InMemoryMigrationRepository,
    MigrationRepository,
    SqlMigrationRepository,
)
from driftless_api.modules.migrations.schemas import AssessmentRun, Migration, MigrationStatus
from driftless_connectors.sdk import SslMode
from driftless_core.errors import ConflictError
from driftless_core.ids import new_id
from driftless_core.schema import Catalog
from driftless_engine.assess import assess

DB_KINDS = ["sqlite", pytest.param("postgres", marks=pytest.mark.integration)]
T0 = datetime(2026, 12, 14, 9, 0, tzinfo=UTC)
SOURCE = "conn_source"


def _connection() -> Connection:
    return Connection(
        id=SOURCE,
        name="src",
        engine="postgres",
        host="h",
        port=5432,
        database="d",
        username="u",
        secret_ref="env:PW",
        ssl_mode=SslMode.PREFER,
        created_at=T0,
        updated_at=T0,
    )


def _migration(name: str, offset: int = 0) -> Migration:
    ts = T0 + timedelta(minutes=offset)
    return Migration(
        id=new_id("mig"),
        name=name,
        source_connection_id=SOURCE,
        source_engine="postgres",
        target_engine="postgres",
        target_connection_id=None,
        status=MigrationStatus.DRAFT,
        created_at=ts,
        updated_at=ts,
    )


@pytest.fixture(params=["memory", *DB_KINDS])
async def repos(
    request: pytest.FixtureRequest, tmp_path: Path, db_factory: Any
) -> AsyncIterator[tuple[MigrationRepository, ConnectionRepository]]:
    if request.param == "memory":
        conns: ConnectionRepository = InMemoryConnectionRepository()
        await conns.add(_connection())
        yield InMemoryMigrationRepository(), conns
        return
    async with db_factory(request.param, tmp_path) as database:
        conns = SqlConnectionRepository(database.sessions)
        await conns.add(_connection())
        yield SqlMigrationRepository(database.sessions), conns


async def test_add_get_list_newest_first(repos: tuple[MigrationRepository, Any]) -> None:
    repo, _ = repos
    old, new = _migration("old", 0), _migration("new", 5)
    await repo.add(old)
    await repo.add(new)
    assert await repo.get(old.id) == old
    assert [m.name for m in await repo.list()] == ["new", "old"]


async def test_names_are_unique(repos: tuple[MigrationRepository, Any]) -> None:
    repo, _ = repos
    await repo.add(_migration("billing"))
    with pytest.raises(ConflictError):
        await repo.add(_migration("billing"))


async def test_status_updates(repos: tuple[MigrationRepository, Any]) -> None:
    repo, _ = repos
    m = _migration("m")
    await repo.add(m)
    later = T0 + timedelta(hours=1)
    await repo.set_status(m.id, MigrationStatus.READY, later)
    loaded = await repo.get(m.id)
    assert loaded is not None
    assert (loaded.status, loaded.updated_at) == (MigrationStatus.READY, later)


async def test_latest_assessment_roundtrip(repos: tuple[MigrationRepository, Any]) -> None:
    repo, _ = repos
    m = _migration("m")
    await repo.add(m)
    assert await repo.latest_assessment(m.id) is None
    result = assess(Catalog(engine="postgres", tables=()), "postgres")
    for minutes in (1, 2):
        await repo.add_assessment(
            AssessmentRun(
                id=new_id("asmt"),
                migration_id=m.id,
                created_at=T0 + timedelta(minutes=minutes),
                assessment=result,
            )
        )
    latest = await repo.latest_assessment(m.id)
    assert latest is not None
    assert latest.created_at == T0 + timedelta(minutes=2)
    assert latest.assessment == result


async def test_uses_connection(repos: tuple[MigrationRepository, Any]) -> None:
    repo, _ = repos
    assert not await repo.uses_connection(SOURCE)
    await repo.add(_migration("m"))
    assert await repo.uses_connection(SOURCE)
