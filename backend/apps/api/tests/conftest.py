from __future__ import annotations

import os
import secrets
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import ClassVar

import psycopg
import pytest
from psycopg import sql

from driftless_api.platform.db import Database
from driftless_connectors.postgres import PostgresTypeMapper
from driftless_connectors.sdk import (
    Capabilities,
    CheckStatus,
    ConnectionCheck,
    ConnectionConfig,
    Connector,
    TypeMapper,
)
from driftless_core.schema import Catalog, Column, DataType, PrimaryKey, Table, TypeKind

PG_URL = os.environ.get("DRIFTLESS_TEST_PG_URL")


class FakeConnector(Connector):
    """Stands in for a real engine: records the config it was built with."""

    engine: ClassVar[str] = "postgres"
    display_name: ClassVar[str] = "PostgreSQL"
    dialect: ClassVar[str] = "postgres"
    default_port: ClassVar[int] = 5432
    capabilities: ClassVar[Capabilities] = Capabilities()
    type_mapper: ClassVar[TypeMapper] = PostgresTypeMapper()
    seen: ClassVar[list[ConnectionConfig]] = []

    def __init__(self, config: ConnectionConfig) -> None:
        super().__init__(config)
        FakeConnector.seen.append(config)

    async def check(self) -> Sequence[ConnectionCheck]:
        if self.config.host == "unreachable":
            return [ConnectionCheck(name="Reachable", status=CheckStatus.FAILED, detail="timeout")]
        return [
            ConnectionCheck(name="Reachable", status=CheckStatus.OK, detail="PostgreSQL 17 · 3 ms"),
            ConnectionCheck(name="Change tracking", status=CheckStatus.WARNING, detail="wal_level"),
        ]

    async def discover(self, schemas: Sequence[str] | None = None) -> Catalog:
        def table(schema: str, name: str, size: int, pk: bool) -> Table:
            return Table(
                schema_name=schema,
                name=name,
                columns=(Column(name="id", type=DataType.of(TypeKind.BIGINT)),),
                primary_key=PrimaryKey(columns=("id",)) if pk else None,
                row_estimate=size // 100,
                size_bytes=size,
            )

        tables = (table("sales", "orders", 9_000, True), table("public", "audit_raw", 500, False))
        if schemas:
            tables = tuple(t for t in tables if t.schema_name in schemas)
        return Catalog(engine="postgres", server_version="17.2", tables=tables)


@pytest.fixture
def fake_connector() -> type[FakeConnector]:
    FakeConnector.seen.clear()
    return FakeConnector


@asynccontextmanager
async def make_database(kind: str, tmp_path: Path) -> AsyncIterator[Database]:
    """A fresh metadata DB: SQLite file, or a throwaway PostgreSQL database."""
    if kind == "sqlite":
        db = Database(f"sqlite+aiosqlite:///{tmp_path}/meta.db")
        await db.create_all()
        try:
            yield db
        finally:
            await db.dispose()
        return
    if not PG_URL:
        pytest.skip("DRIFTLESS_TEST_PG_URL not set")
    name = f"driftless_meta_{secrets.token_hex(4)}"
    with psycopg.connect(PG_URL, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    db = Database(PG_URL.rsplit("/", 1)[0] + f"/{name}")
    await db.create_all()
    try:
        yield db
    finally:
        await db.dispose()
        with psycopg.connect(PG_URL, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name))
            )


@pytest.fixture
def db_factory() -> object:
    """Returns ``make_database`` so tests can open a fresh metadata DB of a given kind."""
    return make_database
