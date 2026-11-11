"""Canonical value normalization.

Different engines render the same value differently (``1`` vs ``true``, ``1.50`` vs
``1.5``, local vs UTC timestamps, Oracle treating ``''`` as NULL). Cross-engine
validation hashes *normalized* values so a row read from SQL Server and the same row
read from PostgreSQL produce identical digests.

The canonical text form is stable and versioned (``NORMALIZATION_VERSION``) — change it
only with a version bump, because stored validation evidence depends on it.
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

NORMALIZATION_VERSION = 1
NULL_TOKEN = "\\N"  # noqa: S105 - COPY-style null marker, not a secret
_FIELD_SEP = "\x1f"  # ASCII unit separator: cannot appear in normalized output unescaped


@dataclass(frozen=True, slots=True)
class NormalizeOptions:
    empty_string_as_null: bool = False
    """Set when either side is Oracle, which stores ``''`` as NULL."""
    decimal_scale: int | None = None
    """Pad/round decimals to a fixed scale (from the column type) before rendering."""


DEFAULT_OPTIONS = NormalizeOptions()


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(_FIELD_SEP, "\\u001f")


def normalize(value: object, options: NormalizeOptions = DEFAULT_OPTIONS) -> str:
    """Render ``value`` in Driftless canonical text form."""
    if value is None:
        return NULL_TOKEN
    match value:
        case bool():
            return "t" if value else "f"
        case int():
            return str(value)
        case Decimal():
            if options.decimal_scale is not None:
                value = value.quantize(Decimal(1).scaleb(-options.decimal_scale))
                return format(value, "f")
            return format(value.normalize(), "f") if value != 0 else "0"
        case float():
            if math.isnan(value):
                return "NaN"
            if math.isinf(value):
                return "Infinity" if value > 0 else "-Infinity"
            return repr(value)
        case datetime():
            if value.tzinfo is not None:
                value = value.astimezone(UTC)
                return value.replace(tzinfo=None).isoformat(timespec="microseconds") + "Z"
            return value.isoformat(timespec="microseconds")
        case date():
            return value.isoformat()
        case time():
            return value.replace(tzinfo=None).isoformat(timespec="microseconds")
        case timedelta():
            return f"{value.total_seconds():.6f}s"
        case uuid.UUID():
            return str(value)
        case bytes() | bytearray() | memoryview():
            return "\\x" + value.hex()
        case str():
            if options.empty_string_as_null and value == "":
                return NULL_TOKEN
            return _escape(value)
        case dict() | list():
            return _escape(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str))
        case _:
            return _escape(str(value))


def row_digest(
    values: Sequence[object], options: Sequence[NormalizeOptions] | NormalizeOptions | None = None
) -> bytes:
    """SHA-256 of one row's normalized values (per-column options optional)."""
    if options is None:
        per_col: Iterable[NormalizeOptions] = (DEFAULT_OPTIONS for _ in values)
    elif isinstance(options, NormalizeOptions):
        per_col = (options for _ in values)
    else:
        if len(options) != len(values):
            raise ValueError("options must have one entry per column")
        per_col = options
    text = _FIELD_SEP.join(normalize(v, o) for v, o in zip(values, per_col, strict=True))
    return hashlib.sha256(text.encode("utf-8")).digest()
