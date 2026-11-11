"""Everything a rule may look at, resolved once per assessment."""

from __future__ import annotations

from dataclasses import dataclass

from driftless_connectors import registry
from driftless_connectors.sdk import Connector
from driftless_core.errors import NotFoundError
from driftless_core.schema import Catalog, Column, Table


@dataclass(frozen=True, slots=True)
class AssessContext:
    catalog: Catalog
    target_engine: str
    source: type[Connector] | None
    target: type[Connector] | None

    @classmethod
    def build(cls, catalog: Catalog, target_engine: str) -> AssessContext:
        return cls(
            catalog=catalog,
            target_engine=target_engine,
            source=_lookup(catalog.engine),
            target=_lookup(target_engine),
        )

    def columns(self) -> list[tuple[Table, Column]]:
        return [(t, c) for t in self.catalog.tables for c in t.columns]

    @property
    def source_name(self) -> str:
        return self.source.display_name if self.source else self.catalog.engine

    @property
    def target_name(self) -> str:
        return self.target.display_name if self.target else self.target_engine


def _lookup(engine: str) -> type[Connector] | None:
    try:
        return registry.get(engine)
    except NotFoundError:
        return None
