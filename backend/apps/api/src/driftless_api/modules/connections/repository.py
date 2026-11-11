"""Persistence port for connections and its two adapters.

``ConnectionRepository`` is the interface the service depends on:

* ``SqlConnectionRepository`` — the metadata DB (PostgreSQL in production).
* ``InMemoryConnectionRepository`` — dev without a database, and fast unit tests.

Both pass the same contract tests (``tests/test_connection_repository.py``).
"""

from __future__ import annotations

from typing import Any, Protocol, cast

from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from driftless_api.modules.connections.models import ConnectionRecord
from driftless_api.modules.connections.schemas import Connection
from driftless_core.errors import ConflictError


class ConnectionRepository(Protocol):
    async def add(self, connection: Connection) -> None: ...
    async def get(self, connection_id: str) -> Connection | None: ...
    async def list(self) -> list[Connection]: ...
    async def delete(self, connection_id: str) -> bool: ...
    async def exists_with_name(self, name: str) -> bool: ...


def _duplicate(name: str) -> ConflictError:
    return ConflictError(f"a connection named {name!r} already exists", details={"name": name})


class InMemoryConnectionRepository:
    def __init__(self) -> None:
        self._items: dict[str, Connection] = {}

    async def add(self, connection: Connection) -> None:
        if await self.exists_with_name(connection.name):
            raise _duplicate(connection.name)
        self._items[connection.id] = connection

    async def get(self, connection_id: str) -> Connection | None:
        return self._items.get(connection_id)

    async def list(self) -> list[Connection]:
        return sorted(self._items.values(), key=lambda c: (c.created_at, c.id))

    async def delete(self, connection_id: str) -> bool:
        return self._items.pop(connection_id, None) is not None

    async def exists_with_name(self, name: str) -> bool:
        return any(c.name == name for c in self._items.values())


class SqlConnectionRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def add(self, connection: Connection) -> None:
        async with self._sessions.begin() as session:
            session.add(ConnectionRecord(**connection.model_dump(mode="python")))
            try:
                await session.flush()
            except IntegrityError as exc:  # unique(name) — the DB is the final arbiter
                raise _duplicate(connection.name) from exc

    async def get(self, connection_id: str) -> Connection | None:
        async with self._sessions() as session:
            record = await session.get(ConnectionRecord, connection_id)
            return Connection.model_validate(record) if record else None

    async def list(self) -> list[Connection]:
        async with self._sessions() as session:
            result = await session.scalars(
                select(ConnectionRecord).order_by(ConnectionRecord.created_at, ConnectionRecord.id)
            )
            return [Connection.model_validate(r) for r in result]

    async def delete(self, connection_id: str) -> bool:
        async with self._sessions.begin() as session:
            result = cast(
                "CursorResult[Any]",
                await session.execute(
                    delete(ConnectionRecord).where(ConnectionRecord.id == connection_id)
                ),
            )
            return result.rowcount > 0

    async def exists_with_name(self, name: str) -> bool:
        async with self._sessions() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(ConnectionRecord)
                .where(ConnectionRecord.name == name)
            )
            return bool(count)
