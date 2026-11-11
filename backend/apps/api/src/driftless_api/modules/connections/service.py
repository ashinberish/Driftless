"""Business rules for connections — framework-free and unit-testable."""

from __future__ import annotations

from datetime import UTC, datetime

from driftless_api.modules.connections.repository import ConnectionRepository
from driftless_api.modules.connections.schemas import Connection, ConnectionCreate
from driftless_connectors import registry
from driftless_core.errors import ConflictError, NotFoundError
from driftless_core.ids import new_id


class ConnectionService:
    def __init__(self, repository: ConnectionRepository) -> None:
        self._repo = repository

    async def create(self, payload: ConnectionCreate) -> Connection:
        registry.get(payload.engine)  # raises NotFoundError for unsupported engines
        if await self._repo.exists_with_name(payload.name):
            raise ConflictError(f"a connection named {payload.name!r} already exists")
        connection = Connection(
            id=new_id("conn"),
            created_at=datetime.now(UTC),
            **payload.model_dump(),
        )
        await self._repo.add(connection)
        return connection

    async def get(self, connection_id: str) -> Connection:
        connection = await self._repo.get(connection_id)
        if connection is None:
            raise NotFoundError(f"connection {connection_id!r} not found")
        return connection

    async def list(self) -> list[Connection]:
        return await self._repo.list()

    async def delete(self, connection_id: str) -> None:
        if not await self._repo.delete(connection_id):
            raise NotFoundError(f"connection {connection_id!r} not found")
