"""Value objects exchanged between connectors and the engine."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class SslMode(StrEnum):
    DISABLE = "disable"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_FULL = "verify-full"


class ConnectionConfig(_Frozen):
    """How to reach a database.

    Production configs carry a ``secret_ref`` (e.g. ``vault:db/billing-ro``) resolved by
    the agent at runtime; ``password`` exists only for local development and tests.
    """

    engine: str
    host: str
    port: int = Field(gt=0, lt=65536)
    database: str
    username: str
    password: SecretStr | None = None
    secret_ref: str | None = None
    ssl_mode: SslMode = SslMode.PREFER
    options: dict[str, str] = Field(default_factory=dict)


class Capabilities(_Frozen):
    """What a connector supports — drives what the UI offers for an engine pair."""

    read: bool = True
    write: bool = False
    cdc: bool = False
    parallel_read: bool = True
    native_checksum: bool = False


class CheckStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    FAILED = "failed"


class ConnectionCheck(_Frozen):
    """One line of the pre-flight checklist shown on the Connect screen."""

    name: str
    status: CheckStatus
    detail: str | None = None
    fix_script: str | None = None


class KeyRange(_Frozen):
    """Half-open primary-key range ``[start, end)``; ``None`` means unbounded."""

    start: tuple[Any, ...] | None = None
    end: tuple[Any, ...] | None = None


class Position(_Frozen):
    """Opaque replication position (LSN, binlog file:offset, SCN...)."""

    engine: str
    token: str


class ChangeOp(StrEnum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class ChangeEvent(_Frozen):
    op: ChangeOp
    table: str
    key: dict[str, Any]
    after: dict[str, Any] | None = None
    position: Position
