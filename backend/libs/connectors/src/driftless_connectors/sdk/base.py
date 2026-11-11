"""Connector contracts.

A connector is one class per engine. It declares what it can do via
:class:`Capabilities` and implements the matching protocol methods. The engine only
ever talks to these protocols, never to a driver directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from typing import Any, ClassVar, Protocol, runtime_checkable

from driftless_connectors.sdk.models import (
    Capabilities,
    ChangeEvent,
    ConnectionCheck,
    ConnectionConfig,
    KeyRange,
    Position,
)
from driftless_core.errors import UnsupportedFeatureError
from driftless_core.schema import Catalog, DataType, Table

Row = tuple[Any, ...]


@runtime_checkable
class TypeMapper(Protocol):
    """Translates between an engine's native type strings and canonical types."""

    def to_canonical(self, native: str) -> DataType: ...

    def to_native(self, data_type: DataType) -> str: ...


class Connector(ABC):
    """Base class for all connectors.

    Subclasses set ``engine``, ``dialect`` (sqlglot dialect name), ``capabilities``
    and ``type_mapper``; then override the operations they support. Unsupported
    operations raise :class:`UnsupportedFeatureError` with a clear message.
    """

    engine: ClassVar[str]
    display_name: ClassVar[str]
    dialect: ClassVar[str]
    default_port: ClassVar[int]
    capabilities: ClassVar[Capabilities]
    type_mapper: ClassVar[TypeMapper]

    def __init__(self, config: ConnectionConfig) -> None:
        if config.engine != self.engine:
            raise ValueError(f"{type(self).__name__} cannot use a {config.engine!r} config")
        self.config = config

    # ---- lifecycle -----------------------------------------------------
    async def __aenter__(self) -> Connector:
        await self.open()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()

    async def open(self) -> None:  # noqa: B027 - optional hook
        """Open pooled resources. Default: nothing to do."""

    async def close(self) -> None:  # noqa: B027 - optional hook
        """Release resources. Default: nothing to do."""

    # ---- read side -----------------------------------------------------
    @abstractmethod
    async def check(self) -> Sequence[ConnectionCheck]:
        """Pre-flight checks: reachability, permissions, CDC readiness."""

    @abstractmethod
    async def discover(self, schemas: Sequence[str] | None = None) -> Catalog:
        """Read the catalog into the canonical schema model."""

    def read_chunk(self, table: Table, key_range: KeyRange) -> AsyncIterator[Sequence[Row]]:
        raise self._unsupported("chunked reads")

    async def snapshot_position(self) -> Position:
        raise self._unsupported("snapshot positions")

    def stream_changes(self, since: Position) -> AsyncIterator[ChangeEvent]:
        raise self._unsupported("change data capture")

    # ---- write side ----------------------------------------------------
    async def apply_ddl(self, statements: Sequence[str]) -> None:
        raise self._unsupported("DDL")

    async def bulk_write(self, table: Table, rows: AsyncIterator[Sequence[Row]]) -> int:
        raise self._unsupported("bulk writes")

    async def apply_changes(self, events: Sequence[ChangeEvent]) -> None:
        raise self._unsupported("applying changes")

    # ---- helpers -------------------------------------------------------
    def _unsupported(self, what: str) -> UnsupportedFeatureError:
        return UnsupportedFeatureError(
            f"{self.display_name} connector does not support {what} yet",
            details={"engine": self.engine, "feature": what},
        )
