"""PostgreSQL <-> canonical type mapping."""

from __future__ import annotations

from driftless_connectors.sdk.parsing import parse_native
from driftless_core.schema import DataType, TypeKind

_SIMPLE: dict[str, TypeKind] = {
    "boolean": TypeKind.BOOLEAN,
    "bool": TypeKind.BOOLEAN,
    "smallint": TypeKind.SMALLINT,
    "int2": TypeKind.SMALLINT,
    "integer": TypeKind.INTEGER,
    "int": TypeKind.INTEGER,
    "int4": TypeKind.INTEGER,
    "bigint": TypeKind.BIGINT,
    "int8": TypeKind.BIGINT,
    "real": TypeKind.REAL,
    "float4": TypeKind.REAL,
    "double precision": TypeKind.DOUBLE,
    "float8": TypeKind.DOUBLE,
    "text": TypeKind.TEXT,
    "bytea": TypeKind.BLOB,
    "date": TypeKind.DATE,
    "interval": TypeKind.INTERVAL,
    "uuid": TypeKind.UUID,
    "json": TypeKind.JSON,
    "jsonb": TypeKind.JSON,
    "xml": TypeKind.XML,
    "geometry": TypeKind.GEOMETRY,
}

_NATIVE: dict[TypeKind, str] = {
    TypeKind.BOOLEAN: "boolean",
    TypeKind.SMALLINT: "smallint",
    TypeKind.INTEGER: "integer",
    TypeKind.BIGINT: "bigint",
    TypeKind.REAL: "real",
    TypeKind.DOUBLE: "double precision",
    TypeKind.TEXT: "text",
    TypeKind.BINARY: "bytea",
    TypeKind.VARBINARY: "bytea",
    TypeKind.BLOB: "bytea",
    TypeKind.DATE: "date",
    TypeKind.INTERVAL: "interval",
    TypeKind.UUID: "uuid",
    TypeKind.JSON: "jsonb",
    TypeKind.XML: "xml",
    TypeKind.GEOMETRY: "geometry",
    TypeKind.ENUM: "text",
    TypeKind.UNKNOWN: "text",
}


class PostgresTypeMapper:
    def to_canonical(self, native: str) -> DataType:
        declaration = native.strip()
        if declaration.endswith("[]"):
            element = self.to_canonical(declaration[:-2])
            return DataType.of(TypeKind.ARRAY, element=element, native=native)

        t = parse_native(declaration)
        base, suffix = t.base, t.suffix
        if base.startswith(("timestamp ", "time ")):
            # "timestamp with time zone" (no precision) parses as one multi-word base.
            base, _, suffix = base.partition(" ")
        if base in _SIMPLE:
            return DataType.of(_SIMPLE[base], native=native)
        if base == "citext":
            return DataType.of(TypeKind.TEXT, case_insensitive=True, native=native)
        if base in {"numeric", "decimal"}:
            return DataType.of(
                TypeKind.DECIMAL, precision=t.int_arg(0), scale=t.int_arg(1), native=native
            )
        if base in {"character varying", "varchar"}:
            return DataType.of(TypeKind.VARCHAR, length=t.int_arg(0), native=native)
        if base in {"character", "char", "bpchar"}:
            return DataType.of(TypeKind.CHAR, length=t.int_arg(0) or 1, native=native)
        if base in {"timestamp", "time"}:
            with_tz = suffix.startswith("with time zone")
            if base == "timestamp":
                kind = TypeKind.TIMESTAMP_TZ if with_tz else TypeKind.TIMESTAMP
            else:
                kind = TypeKind.TIME  # time with time zone is discouraged; treat as TIME
            return DataType.of(kind, precision=t.int_arg(0), native=native)
        if base in {"timestamptz"}:
            return DataType.of(TypeKind.TIMESTAMP_TZ, precision=t.int_arg(0), native=native)
        return DataType.of(TypeKind.UNKNOWN, native=native)

    def to_native(self, data_type: DataType) -> str:
        k = data_type.kind
        match k:
            case TypeKind.DECIMAL:
                if data_type.precision is None:
                    return "numeric"
                return f"numeric({data_type.precision},{data_type.scale or 0})"
            case TypeKind.VARCHAR:
                if data_type.case_insensitive:
                    return "citext"
                return f"varchar({data_type.length})" if data_type.length else "varchar"
            case TypeKind.CHAR:
                return f"char({data_type.length or 1})"
            case TypeKind.TEXT if data_type.case_insensitive:
                return "citext"
            case TypeKind.TIME | TypeKind.TIMESTAMP | TypeKind.TIMESTAMP_TZ:
                base = "time" if k is TypeKind.TIME else "timestamp"
                # PostgreSQL supports at most microsecond precision.
                p = min(data_type.precision, 6) if data_type.precision is not None else None
                rendered = f"{base}({p})" if p is not None else base
                return rendered + (" with time zone" if k is TypeKind.TIMESTAMP_TZ else "")
            case TypeKind.ARRAY:
                assert data_type.element is not None
                return f"{self.to_native(data_type.element)}[]"
            case _:
                return _NATIVE[k]
