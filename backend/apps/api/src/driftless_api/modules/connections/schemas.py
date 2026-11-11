"""Request/response contracts for the connections API (what the frontend sees)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from driftless_connectors.sdk import SslMode


class ConnectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    engine: str
    host: str
    port: int = Field(gt=0, lt=65536)
    database: str
    username: str
    secret_ref: str = Field(
        description="Reference to the credential in the secrets backend, e.g. vault:db/billing-ro",
        pattern=r"^[a-z]+:.+",
    )
    ssl_mode: SslMode = SslMode.PREFER


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


class Page[T](BaseModel):
    items: list[T]
    total: int
