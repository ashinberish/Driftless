"""PostgreSQL connector (psycopg 3, async).

S1 scope: pre-flight checks and catalog discovery. Chunked reads, COPY writes and
logical-replication CDC land in S4/S7 (see docs/execution-plan.md).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ClassVar

from driftless_connectors.postgres import queries
from driftless_connectors.postgres.type_map import PostgresTypeMapper
from driftless_connectors.sdk.base import Connector, TypeMapper
from driftless_connectors.sdk.models import Capabilities, CheckStatus, ConnectionCheck
from driftless_connectors.sdk.registry import registry
from driftless_core.errors import ConfigurationError, ConnectionFailedError
from driftless_core.schema import Catalog, Column, ForeignKey, PrimaryKey, Table

if TYPE_CHECKING:
    from psycopg import AsyncConnection


@registry.register
class PostgresConnector(Connector):
    engine: ClassVar[str] = "postgres"
    display_name: ClassVar[str] = "PostgreSQL"
    dialect: ClassVar[str] = "postgres"
    default_port: ClassVar[int] = 5432
    capabilities: ClassVar[Capabilities] = Capabilities(read=True, write=True, cdc=True)
    type_mapper: ClassVar[TypeMapper] = PostgresTypeMapper()

    async def _connect(self) -> AsyncConnection[Any]:
        try:
            import psycopg
        except ImportError as exc:  # pragma: no cover - depends on install extras
            raise ConfigurationError(
                "PostgreSQL support needs the 'postgres' extra: driftless-connectors[postgres]"
            ) from exc
        if self.config.password is None:
            raise ConfigurationError("resolve secret_ref to a password before connecting")
        try:
            return await psycopg.AsyncConnection.connect(
                host=self.config.host,
                port=self.config.port,
                dbname=self.config.database,
                user=self.config.username,
                password=self.config.password.get_secret_value(),
                sslmode=self.config.ssl_mode.value,
                connect_timeout=10,
                application_name="driftless",
            )
        except psycopg.OperationalError as exc:
            raise ConnectionFailedError(str(exc), details={"host": self.config.host}) from exc

    async def check(self) -> Sequence[ConnectionCheck]:
        checks: list[ConnectionCheck] = []
        async with await self._connect() as conn:
            checks.append(ConnectionCheck(name="Reachable", status=CheckStatus.OK))
            cur = await conn.execute(queries.WAL_LEVEL)
            row = await cur.fetchone()
            wal_level = row[0] if row else "unknown"
            if wal_level == "logical":
                checks.append(ConnectionCheck(name="Change tracking", status=CheckStatus.OK))
            else:
                checks.append(
                    ConnectionCheck(
                        name="Change tracking",
                        status=CheckStatus.WARNING,
                        detail=f"wal_level is {wal_level!r}; zero-downtime needs 'logical'",
                        fix_script="ALTER SYSTEM SET wal_level = 'logical';  -- then restart",
                    )
                )
        return checks

    async def discover(self, schemas: Sequence[str] | None = None) -> Catalog:
        scope = list(schemas) if schemas else None
        async with await self._connect() as conn:
            version_row = await (await conn.execute("SHOW server_version")).fetchone()
            columns = await (await conn.execute(queries.COLUMNS, {"schemas": scope})).fetchall()
            pks = await (await conn.execute(queries.PRIMARY_KEYS, {"schemas": scope})).fetchall()
            fks = await (await conn.execute(queries.FOREIGN_KEYS, {"schemas": scope})).fetchall()
            stats = await (await conn.execute(queries.TABLE_STATS, {"schemas": scope})).fetchall()

        cols_by_table: dict[tuple[str, str], list[Column]] = defaultdict(list)
        for schema, table, name, type_decl, not_null, default, identity in columns:
            cols_by_table[(schema, table)].append(
                Column(
                    name=name,
                    type=self.type_mapper.to_canonical(type_decl),
                    nullable=not not_null,
                    default=default,
                    identity=bool(identity),
                )
            )
        pk_by_table = {(s, t): PrimaryKey(name=n, columns=tuple(c)) for s, t, n, c in pks}
        fk_by_table: dict[tuple[str, str], list[ForeignKey]] = defaultdict(list)
        for s, t, name, cols, ref_s, ref_t, ref_cols in fks:
            fk_by_table[(s, t)].append(
                ForeignKey(
                    name=name,
                    columns=tuple(cols),
                    ref_schema=ref_s,
                    ref_table=ref_t,
                    ref_columns=tuple(ref_cols),
                )
            )
        stats_by_table = {(s, t): (rows, size) for s, t, rows, size in stats}

        tables = tuple(
            Table(
                schema_name=s,
                name=t,
                columns=tuple(cols),
                primary_key=pk_by_table.get((s, t)),
                foreign_keys=tuple(fk_by_table.get((s, t), ())),
                row_estimate=stats_by_table.get((s, t), (None, None))[0],
                size_bytes=stats_by_table.get((s, t), (None, None))[1],
            )
            for (s, t), cols in sorted(cols_by_table.items())
        )
        return Catalog(
            engine=self.engine,
            server_version=version_row[0] if version_row else None,
            tables=tables,
        )
