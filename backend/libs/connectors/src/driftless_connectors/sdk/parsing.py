"""Helpers for parsing native type declarations like ``numeric(19, 4)``."""

from __future__ import annotations

import re
from dataclasses import dataclass

_TYPE_RE = re.compile(r"^\s*(?P<base>[^()]+?)\s*(?:\((?P<args>[^)]*)\)\s*(?P<rest>.*?))?\s*$")


@dataclass(frozen=True, slots=True)
class NativeType:
    base: str
    args: tuple[str, ...]
    suffix: str

    def int_arg(self, index: int) -> int | None:
        if index >= len(self.args):
            return None
        raw = self.args[index].strip()
        return int(raw) if raw.isdigit() else None


def parse_native(declaration: str) -> NativeType:
    """Split ``"timestamp(3) with time zone"`` into base, args and suffix.

    Base and suffix are lower-cased and whitespace-collapsed; arguments are kept as-is
    (enum labels are case-sensitive).
    """
    match = _TYPE_RE.match(declaration)
    if match is None:
        raise ValueError(f"cannot parse type declaration {declaration!r}")
    base = " ".join(match["base"].lower().split())
    raw_args = match["args"]
    args = tuple(_split_args(raw_args)) if raw_args else ()
    suffix = " ".join((match["rest"] or "").lower().split())
    return NativeType(base=base, args=args, suffix=suffix)


def _split_args(raw: str) -> list[str]:
    """Split on commas that are not inside single quotes (enum labels)."""
    parts: list[str] = []
    buf: list[str] = []
    quoted = False
    for ch in raw:
        if ch == "'":
            quoted = not quoted
        if ch == "," and not quoted:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf).strip())
    return parts
