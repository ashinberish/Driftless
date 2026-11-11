"""MySQL connector.

Registered now so the UI can offer MySQL and the type mapping can be exercised by the
conversion engine; network operations arrive in S6 (see docs/execution-plan.md).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from driftless_connectors.mysql.type_map import MySQLTypeMapper
from driftless_connectors.sdk.base import Connector, TypeMapper
from driftless_connectors.sdk.models import Capabilities, ConnectionCheck
from driftless_connectors.sdk.registry import registry
from driftless_core.schema import Catalog


@registry.register
class MySQLConnector(Connector):
    engine: ClassVar[str] = "mysql"
    display_name: ClassVar[str] = "MySQL"
    dialect: ClassVar[str] = "mysql"
    default_port: ClassVar[int] = 3306
    capabilities: ClassVar[Capabilities] = Capabilities(read=True, write=False, cdc=False)
    type_mapper: ClassVar[TypeMapper] = MySQLTypeMapper()

    async def check(self) -> Sequence[ConnectionCheck]:
        raise self._unsupported("connection checks")

    async def discover(self, schemas: Sequence[str] | None = None) -> Catalog:
        raise self._unsupported("discovery")
