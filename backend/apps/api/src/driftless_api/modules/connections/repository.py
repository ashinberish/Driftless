"""Persistence port for connections.

``ConnectionRepository`` is the interface the service depends on. The in-memory
implementation backs local dev and tests; the SQLAlchemy implementation (metadata DB)
replaces it in S1 without touching the service or router.
"""

from __future__ import annotations

from typing import Protocol

from driftless_api.modules.connections.schemas import Connection


class ConnectionRepository(Protocol):
    async def add(self, connection: Connection) -> None: ...
    async def get(self, connection_id: str) -> Connection | None: ...
    async def list(self) -> list[Connection]: ...
    async def delete(self, connection_id: str) -> bool: ...
    async def exists_with_name(self, name: str) -> bool: ...


class InMemoryConnectionRepository:
    def __init__(self) -> None:
        self._items: dict[str, Connection] = {}

    async def add(self, connection: Connection) -> None:
        self._items[connection.id] = connection

    async def get(self, connection_id: str) -> Connection | None:
        return self._items.get(connection_id)

    async def list(self) -> list[Connection]:
        return sorted(self._items.values(), key=lambda c: c.created_at)

    async def delete(self, connection_id: str) -> bool:
        return self._items.pop(connection_id, None) is not None

    async def exists_with_name(self, name: str) -> bool:
        return any(c.name == name for c in self._items.values())
