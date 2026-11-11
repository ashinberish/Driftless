"""MySQL <-> canonical type mapping."""

from __future__ import annotations

from driftless_connectors.sdk.parsing import parse_native
from driftless_core.schema import DataType, TypeKind

_SIMPLE: dict[str, TypeKind] = {
    "bool": TypeKind.BOOLEAN,
    "boolean": TypeKind.BOOLEAN,
    "smallint": TypeKind.SMALLINT,
    "mediumint": TypeKind.INTEGER,
    "int": TypeKind.INTEGER,
    "integer": TypeKind.INTEGER,
    "bigint": TypeKind.BIGINT,
    "float": TypeKind.REAL,
    "double": TypeKind.DOUBLE,
    "double precision": TypeKind.DOUBLE,
    "tinytext": TypeKind.TEXT,
    "text": TypeKind.TEXT,
    "mediumtext": TypeKind.TEXT,
    "longtext": TypeKind.TEXT,
    "tinyblob": TypeKind.BLOB,
    "blob": TypeKind.BLOB,
    "mediumblob": TypeKind.BLOB,
    "longblob": TypeKind.BLOB,
    "date": TypeKind.DATE,
    "json": TypeKind.JSON,
    "geometry": TypeKind.GEOMETRY,
}

_NATIVE: dict[TypeKind, str] = {
    TypeKind.BOOLEAN: "tinyint(1)",
    TypeKind.SMALLINT: "smallint",
    TypeKind.INTEGER: "int",
    TypeKind.BIGINT: "bigint",
    TypeKind.REAL: "float",
    TypeKind.DOUBLE: "double",
    TypeKind.TEXT: "longtext",
    TypeKind.BLOB: "longblob",
    TypeKind.DATE: "date",
    TypeKind.INTERVAL: "varchar(64)",
    TypeKind.UUID: "char(36)",
    TypeKind.JSON: "json",
    TypeKind.XML: "longtext",
    TypeKind.GEOMETRY: "geometry",
    TypeKind.ARRAY: "json",
    TypeKind.UNKNOWN: "longtext",
}


class MySQLTypeMapper:
    def to_canonical(self, native: str) -> DataType:
        t = parse_native(native)
        base = t.base.removesuffix(" unsigned")
        unsigned = "unsigned" in t.suffix or t.base.endswith(" unsigned")

        if base == "tinyint":
            # tinyint(1) is MySQL's conventional boolean.
            if t.int_arg(0) == 1:
                return DataType.of(TypeKind.BOOLEAN, native=native)
            return DataType.of(TypeKind.SMALLINT, native=native)
        if base in {"int", "integer", "mediumint"} and unsigned:
            return DataType.of(TypeKind.BIGINT, native=native)  # widen to avoid overflow
        if base == "bigint" and unsigned:
            return DataType.of(TypeKind.DECIMAL, precision=20, scale=0, native=native)
        if base in _SIMPLE:
            return DataType.of(_SIMPLE[base], native=native)
        if base in {"decimal", "numeric"}:
            return DataType.of(
                TypeKind.DECIMAL,
                precision=t.int_arg(0) or 10,
                scale=t.int_arg(1) or 0,
                native=native,
            )
        if base == "varchar":
            return DataType.of(TypeKind.VARCHAR, length=t.int_arg(0), native=native)
        if base == "char":
            return DataType.of(TypeKind.CHAR, length=t.int_arg(0) or 1, native=native)
        if base == "binary":
            return DataType.of(TypeKind.BINARY, length=t.int_arg(0) or 1, native=native)
        if base == "varbinary":
            return DataType.of(TypeKind.VARBINARY, length=t.int_arg(0), native=native)
        if base == "datetime":
            return DataType.of(TypeKind.TIMESTAMP, precision=t.int_arg(0), native=native)
        if base == "timestamp":
            # MySQL TIMESTAMP is stored in UTC and converted to the session time zone.
            return DataType.of(TypeKind.TIMESTAMP_TZ, precision=t.int_arg(0), native=native)
        if base == "time":
            return DataType.of(TypeKind.TIME, precision=t.int_arg(0), native=native)
        if base == "year":
            return DataType.of(TypeKind.SMALLINT, native=native)
        if base in {"enum", "set"}:
            labels = tuple(a.strip("'") for a in t.args)
            return DataType.of(TypeKind.ENUM, enum_values=labels, native=native)
        return DataType.of(TypeKind.UNKNOWN, native=native)

    def to_native(self, data_type: DataType) -> str:
        k = data_type.kind
        match k:
            case TypeKind.DECIMAL:
                # MySQL caps DECIMAL at 65 digits.
                p = min(data_type.precision or 65, 65)
                return f"decimal({p},{data_type.scale or 0})"
            case TypeKind.VARCHAR:
                return f"varchar({data_type.length or 255})"
            case TypeKind.CHAR:
                return f"char({data_type.length or 1})"
            case TypeKind.BINARY:
                return f"binary({data_type.length or 1})"
            case TypeKind.VARBINARY:
                return f"varbinary({data_type.length or 255})"
            case TypeKind.TIME | TypeKind.TIMESTAMP | TypeKind.TIMESTAMP_TZ:
                base = {TypeKind.TIME: "time", TypeKind.TIMESTAMP: "datetime"}.get(k, "datetime")
                p = min(data_type.precision, 6) if data_type.precision is not None else None
                return f"{base}({p})" if p is not None else base
            case TypeKind.ENUM:
                assert data_type.enum_values is not None
                labels = ",".join("'" + v.replace("'", "''") + "'" for v in data_type.enum_values)
                return f"enum({labels})"
            case _:
                return _NATIVE[k]
