"""Contract tests: every ConnectionRepository implementation must behave the same."""

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
from driftless_connectors.sdk import SslMode
from driftless_core.errors import ConflictError
from driftless_core.ids import new_id

DB_KINDS = ["sqlite", pytest.param("postgres", marks=pytest.mark.integration)]

T0 = datetime(2026, 11, 30, 9, 0, tzinfo=UTC)


def _conn(name: str, offset: int = 0) -> Connection:
    ts = T0 + timedelta(minutes=offset)
    return Connection(
        id=new_id("conn"),
        name=name,
        engine="postgres",
        host="db.internal",
        port=5432,
        database="app",
        username="ro",
        secret_ref="env:PW",
        ssl_mode=SslMode.REQUIRE,
        created_at=ts,
        updated_at=ts,
    )


@pytest.fixture(params=["memory", *DB_KINDS])
async def repo(
    request: pytest.FixtureRequest, tmp_path: Path, db_factory: Any
) -> AsyncIterator[ConnectionRepository]:
    if request.param == "memory":
        yield InMemoryConnectionRepository()
        return
    async with db_factory(request.param, tmp_path) as database:
        yield SqlConnectionRepository(database.sessions)


async def test_add_get_roundtrip_preserves_fields(repo: ConnectionRepository) -> None:
    conn = _conn("billing")
    await repo.add(conn)
    loaded = await repo.get(conn.id)
    assert loaded == conn
    assert loaded is not None
    assert loaded.created_at.tzinfo is not None


async def test_list_is_ordered_by_creation(repo: ConnectionRepository) -> None:
    b, a = _conn("b", offset=5), _conn("a", offset=1)
    await repo.add(b)
    await repo.add(a)
    assert [c.name for c in await repo.list()] == ["a", "b"]


async def test_names_are_unique(repo: ConnectionRepository) -> None:
    await repo.add(_conn("billing"))
    assert await repo.exists_with_name("billing")
    with pytest.raises(ConflictError):
        await repo.add(_conn("billing"))


async def test_delete(repo: ConnectionRepository) -> None:
    conn = _conn("tmp")
    await repo.add(conn)
    assert await repo.delete(conn.id)
    assert not await repo.delete(conn.id)
    assert await repo.get(conn.id) is None
