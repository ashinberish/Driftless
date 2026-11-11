"""Request/response contracts for the connections API (what the frontend sees)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from driftless_connectors.sdk import ConnectionCheck, SslMode


class ConnectionSpec(BaseModel):
    """How to reach a database. Used to test a connection before saving it."""

    engine: str = Field(min_length=1, max_length=32)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(gt=0, lt=65536)
    database: str = Field(min_length=1, max_length=255)
    username: str = Field(min_length=1, max_length=255)
    secret_ref: str = Field(
        max_length=512,
        description="Reference to the credential in a secrets backend, e.g. vault:db/billing-ro",
        pattern=r"^[a-z][a-z0-9+-]*:\S.*$",
    )
    ssl_mode: SslMode = SslMode.PREFER


class ConnectionCreate(ConnectionSpec):
    name: str = Field(min_length=1, max_length=120, pattern=r"^\S(.*\S)?$")


class Connection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    engine: str
    host: str
    port: int
    database: str
    username: str
    secret_ref: str
    ssl_mode: SslMode
    created_at: datetime
    updated_at: datetime


class ConnectionTestResult(BaseModel):
    ok: bool = Field(description="True when no check failed (warnings are allowed)")
    checks: list[ConnectionCheck]


class TableSummary(BaseModel):
    name: str
    columns: int
    rows: int | None
    size_bytes: int | None
    has_primary_key: bool


class CatalogSummary(BaseModel):
    engine: str
    server_version: str | None
    schemas: list[str]
    total_tables: int
    total_rows: int
    total_bytes: int
    tables: list[TableSummary]


class Page[T](BaseModel):
    items: list[T]
    total: int
