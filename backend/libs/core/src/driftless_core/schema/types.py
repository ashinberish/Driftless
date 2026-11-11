"""Canonical (engine-neutral) data types.

Every connector maps its native types *to* and *from* this model. Conversion between
any two engines therefore goes ``source native -> DataType -> target native`` and each
new engine costs one mapping instead of one per engine pair.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator


class TypeKind(StrEnum):
    BOOLEAN = "boolean"
    SMALLINT = "smallint"
    INTEGER = "integer"
    BIGINT = "bigint"
    DECIMAL = "decimal"
    REAL = "real"
    DOUBLE = "double"
    CHAR = "char"
    VARCHAR = "varchar"
    TEXT = "text"
    BINARY = "binary"
    VARBINARY = "varbinary"
    BLOB = "blob"
    DATE = "date"
    TIME = "time"
    TIMESTAMP = "timestamp"
    TIMESTAMP_TZ = "timestamp_tz"
    INTERVAL = "interval"
    UUID = "uuid"
    JSON = "json"
    XML = "xml"
    ENUM = "enum"
    ARRAY = "array"
    GEOMETRY = "geometry"
    UNKNOWN = "unknown"


_LENGTH_KINDS = {TypeKind.CHAR, TypeKind.VARCHAR, TypeKind.BINARY, TypeKind.VARBINARY}
_TEMPORAL_PRECISION_KINDS = {TypeKind.TIME, TypeKind.TIMESTAMP, TypeKind.TIMESTAMP_TZ}
INTEGER_KINDS = frozenset({TypeKind.SMALLINT, TypeKind.INTEGER, TypeKind.BIGINT})
TEXT_KINDS = frozenset({TypeKind.CHAR, TypeKind.VARCHAR, TypeKind.TEXT})


class DataType(BaseModel):
    """An engine-neutral column type.

    ``precision`` means total digits for DECIMAL and fractional-second digits for
    TIME/TIMESTAMP types. ``native`` keeps the original declaration for reporting.
    """

    model_config = ConfigDict(frozen=True)

    kind: TypeKind
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    case_insensitive: bool = False
    element: DataType | None = None
    enum_values: tuple[str, ...] | None = None
    native: str | None = None

    @model_validator(mode="after")
    def _check_params(self) -> DataType:
        if self.length is not None and self.kind not in _LENGTH_KINDS:
            raise ValueError(f"length is not valid for {self.kind}")
        if self.scale is not None and self.kind is not TypeKind.DECIMAL:
            raise ValueError(f"scale is only valid for decimal, not {self.kind}")
        if self.precision is not None and self.kind not in (
            {TypeKind.DECIMAL} | _TEMPORAL_PRECISION_KINDS
        ):
            raise ValueError(f"precision is not valid for {self.kind}")
        if self.kind is TypeKind.ARRAY and self.element is None:
            raise ValueError("array types need an element type")
        if self.kind is TypeKind.ENUM and not self.enum_values:
            raise ValueError("enum types need enum_values")
        return self

    # Convenience constructors keep call sites short and readable.
    @classmethod
    def of(cls, kind: TypeKind, **params: object) -> DataType:
        return cls.model_validate({"kind": kind, **params})

    def __str__(self) -> str:
        args: list[str] = []
        if self.length is not None:
            args.append(str(self.length))
        if self.precision is not None:
            args.append(str(self.precision))
        if self.scale is not None:
            args.append(str(self.scale))
        base = self.kind.value + (f"({', '.join(args)})" if args else "")
        if self.kind is TypeKind.ARRAY and self.element is not None:
            base = f"{self.element}[]"
        return base + (" ci" if self.case_insensitive else "")
