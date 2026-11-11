"""Generate target DDL from the canonical schema.

Types come from the target connector's ``TypeMapper``; identifier quoting and statement
rendering come from sqlglot, so every engine gets correct syntax without hand-written
string templates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

import sqlglot
from sqlglot import exp

from driftless_connectors.sdk import Connector
from driftless_core.schema import Table

_CAMEL_1 = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL_2 = re.compile(r"([a-z0-9])([A-Z])")


class NamingStyle(StrEnum):
    SNAKE_CASE = "snake_case"
    PRESERVE = "preserve"


def to_snake_case(name: str) -> str:
    return _CAMEL_2.sub(r"\1_\2", _CAMEL_1.sub(r"\1_\2", name)).replace("__", "_").lower()


@dataclass(frozen=True, slots=True)
class DdlGenerator:
    target: type[Connector]
    naming: NamingStyle = NamingStyle.SNAKE_CASE
    target_schema: str | None = None

    def name(self, identifier: str) -> str:
        return to_snake_case(identifier) if self.naming is NamingStyle.SNAKE_CASE else identifier

    def _ident(self, identifier: str) -> exp.Identifier:
        return exp.to_identifier(self.name(identifier), quoted=self.naming is NamingStyle.PRESERVE)

    def create_table(self, table: Table) -> str:
        """``CREATE TABLE`` with columns and primary key only.

        Indexes and foreign keys are created *after* the bulk copy (see
        :meth:`post_copy`) because loading into an unindexed table is much faster.
        """
        mapper = self.target.type_mapper
        columns: list[exp.Expr] = []
        for col in table.columns:
            constraints: list[exp.ColumnConstraint] = []
            if not col.nullable:
                constraints.append(exp.ColumnConstraint(kind=exp.NotNullColumnConstraint()))
            columns.append(
                exp.ColumnDef(
                    this=self._ident(col.name),
                    kind=exp.DataType.build(
                        mapper.to_native(col.type), dialect=self.target.dialect, udt=True
                    ),
                    constraints=constraints,
                )
            )
        if table.primary_key:
            columns.append(
                exp.PrimaryKey(expressions=[self._ident(c) for c in table.primary_key.columns])
            )
        schema = exp.Schema(this=self._table_ref(table), expressions=columns)
        return exp.Create(this=schema, kind="TABLE").sql(dialect=self.target.dialect)

    def post_copy(self, table: Table) -> list[str]:
        """Index and foreign-key statements to run after data is loaded."""
        statements: list[str] = []
        table_sql = self._table_ref(table).sql(dialect=self.target.dialect)
        for idx in table.indexes:
            cols = ", ".join(self._ident(c).sql(dialect=self.target.dialect) for c in idx.columns)
            unique = "UNIQUE " if idx.unique else ""
            name = self._ident(idx.name).sql(dialect=self.target.dialect)
            statements.append(f"CREATE {unique}INDEX {name} ON {table_sql} ({cols})")
        for fk in table.foreign_keys:
            ref = exp.table_(self.name(fk.ref_table), db=self.target_schema or fk.ref_schema).sql(
                dialect=self.target.dialect
            )
            cols = ", ".join(self._ident(c).sql(dialect=self.target.dialect) for c in fk.columns)
            ref_cols = ", ".join(
                self._ident(c).sql(dialect=self.target.dialect) for c in fk.ref_columns
            )
            statements.append(
                f"ALTER TABLE {table_sql} ADD FOREIGN KEY ({cols}) REFERENCES {ref} ({ref_cols})"
            )
        # Round-trip through sqlglot to validate syntax for the target dialect.
        return [
            sqlglot.transpile(s, read=self.target.dialect, write=self.target.dialect)[0]
            for s in statements
        ]

    def _table_ref(self, table: Table) -> exp.Table:
        schema = self.target_schema if self.target_schema is not None else table.schema_name
        return exp.Table(
            this=self._ident(table.name),
            db=exp.to_identifier(schema) if schema else None,
        )
