"""Canonical schema model: what a connector's ``discover`` returns and what DDL
generators consume. Immutable so it can be shared safely across workers."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from driftless_core.schema.types import DataType


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class ReferentialAction(StrEnum):
    NO_ACTION = "no_action"
    RESTRICT = "restrict"
    CASCADE = "cascade"
    SET_NULL = "set_null"
    SET_DEFAULT = "set_default"


class Column(_Frozen):
    name: str
    type: DataType
    nullable: bool = True
    default: str | None = None
    identity: bool = False
    comment: str | None = None


class PrimaryKey(_Frozen):
    name: str | None = None
    columns: tuple[str, ...]


class ForeignKey(_Frozen):
    name: str | None = None
    columns: tuple[str, ...]
    ref_schema: str | None = None
    ref_table: str
    ref_columns: tuple[str, ...]
    on_delete: ReferentialAction = ReferentialAction.NO_ACTION
    on_update: ReferentialAction = ReferentialAction.NO_ACTION


class Index(_Frozen):
    name: str
    columns: tuple[str, ...]
    unique: bool = False


class Table(_Frozen):
    schema_name: str | None = None
    name: str
    columns: tuple[Column, ...]
    primary_key: PrimaryKey | None = None
    foreign_keys: tuple[ForeignKey, ...] = ()
    indexes: tuple[Index, ...] = ()
    row_estimate: int | None = None
    size_bytes: int | None = None

    @property
    def qualified_name(self) -> str:
        return f"{self.schema_name}.{self.name}" if self.schema_name else self.name

    @property
    def has_primary_key(self) -> bool:
        return self.primary_key is not None and len(self.primary_key.columns) > 0

    def column(self, name: str) -> Column:
        for col in self.columns:
            if col.name == name:
                return col
        raise KeyError(f"{self.qualified_name} has no column {name!r}")


class Catalog(_Frozen):
    """Everything discovered in one database (or the selected scope of it)."""

    engine: str
    server_version: str | None = None
    tables: tuple[Table, ...] = Field(default=())

    def table(self, qualified_name: str) -> Table:
        for table in self.tables:
            if table.qualified_name == qualified_name:
                return table
        raise KeyError(f"no table {qualified_name!r} in catalog")

    @property
    def total_rows(self) -> int:
        return sum(t.row_estimate or 0 for t in self.tables)

    @property
    def total_bytes(self) -> int:
        return sum(t.size_bytes or 0 for t in self.tables)
