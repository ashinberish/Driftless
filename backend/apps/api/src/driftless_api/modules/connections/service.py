"""Business rules for connections — framework-free and unit-testable.

Collaborators are injected: a repository (persistence), a secret registry (resolves
``secret_ref`` only at connect time) and a connector factory (engine drivers).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from driftless_api.modules.connections.repository import ConnectionRepository
from driftless_api.modules.connections.schemas import (
    CatalogSummary,
    Connection,
    ConnectionCreate,
    ConnectionSpec,
    ConnectionTestResult,
    TableSummary,
)
from driftless_connectors import registry
from driftless_connectors.sdk import CheckStatus, ConnectionCheck, ConnectionConfig, Connector
from driftless_core.errors import ConfigurationError, ConflictError, NotFoundError
from driftless_core.ids import new_id
from driftless_core.schema import Catalog
from driftless_core.secrets import SecretNotFoundError, SecretResolverRegistry

type ConnectorFactory = Callable[[ConnectionConfig], Connector]
type InUseCheck = Callable[[str], Awaitable[bool]]


class ConnectionService:
    def __init__(
        self,
        repository: ConnectionRepository,
        secrets: SecretResolverRegistry,
        connector_factory: ConnectorFactory = registry.create,
        in_use: InUseCheck | None = None,
    ) -> None:
        self._repo = repository
        self._secrets = secrets
        self._connector_factory = connector_factory
        self._in_use = in_use

    # ------------------------------------------------------------------ CRUD
    async def create(self, payload: ConnectionCreate) -> Connection:
        registry.get(payload.engine)  # NotFoundError for unsupported engines
        self._require_supported_secret(payload.secret_ref)
        if await self._repo.exists_with_name(payload.name):
            raise ConflictError(
                f"a connection named {payload.name!r} already exists",
                details={"name": payload.name},
            )
        now = datetime.now(UTC)
        connection = Connection(
            id=new_id("conn"), created_at=now, updated_at=now, **payload.model_dump()
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
        if self._in_use is not None and await self._in_use(connection_id):
            raise ConflictError(
                "this connection is used by a migration; delete the migration first",
                details={"connection_id": connection_id},
            )
        if not await self._repo.delete(connection_id):
            raise NotFoundError(f"connection {connection_id!r} not found")

    # ------------------------------------------------------------ live checks
    async def test_spec(self, spec: ConnectionSpec | Connection) -> ConnectionTestResult:
        """Run pre-flight checks for a connection that may not be saved yet."""
        registry.get(spec.engine)
        try:
            config = await self._config(spec)
        except (SecretNotFoundError, ConfigurationError) as exc:
            # Credential problems are a check result, not a server error.
            check = ConnectionCheck(
                name="Credentials", status=CheckStatus.FAILED, detail=exc.message
            )
            return ConnectionTestResult(ok=False, checks=[check])
        checks = list(await self._connector_factory(config).check())
        return ConnectionTestResult(
            ok=all(c.status is not CheckStatus.FAILED for c in checks), checks=checks
        )

    async def test(self, connection_id: str) -> ConnectionTestResult:
        return await self.test_spec(await self.get(connection_id))

    async def catalog(self, connection_id: str, schemas: list[str] | None = None) -> Catalog:
        """Full canonical catalog of a saved connection (used by assessments)."""
        connection = await self.get(connection_id)
        connector = self._connector_factory(await self._config(connection))
        return await connector.discover(schemas)

    async def discover(
        self, connection_id: str, schemas: list[str] | None = None
    ) -> CatalogSummary:
        catalog = await self.catalog(connection_id, schemas)
        return CatalogSummary(
            engine=catalog.engine,
            server_version=catalog.server_version,
            schemas=sorted({t.schema_name for t in catalog.tables if t.schema_name}),
            total_tables=len(catalog.tables),
            total_rows=catalog.total_rows,
            total_bytes=catalog.total_bytes,
            tables=[
                TableSummary(
                    name=t.qualified_name,
                    columns=len(t.columns),
                    rows=t.row_estimate,
                    size_bytes=t.size_bytes,
                    has_primary_key=t.has_primary_key,
                )
                for t in sorted(catalog.tables, key=lambda t: -(t.size_bytes or 0))
            ],
        )

    # ---------------------------------------------------------------- helpers
    def _require_supported_secret(self, reference: str) -> None:
        if not self._secrets.supports(reference):
            raise ConfigurationError(
                f"secret backend for {reference.split(':', 1)[0]!r} is not configured",
                details={"available": self._secrets.schemes},
            )

    async def _config(self, spec: ConnectionSpec | Connection) -> ConnectionConfig:
        password = await self._secrets.resolve(spec.secret_ref)
        return ConnectionConfig(
            engine=spec.engine,
            host=spec.host,
            port=spec.port,
            database=spec.database,
            username=spec.username,
            password=password,
            secret_ref=spec.secret_ref,
            ssl_mode=spec.ssl_mode,
        )
