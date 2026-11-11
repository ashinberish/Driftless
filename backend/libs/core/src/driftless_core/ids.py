"""Prefixed, time-sortable identifiers, e.g. ``mig_01jcf3q8k2v7...``.

The prefix makes IDs self-describing in logs and URLs; the body is ULID-style
(48-bit millisecond timestamp + 80 random bits, Crockford base32) so IDs sort by
creation time.
"""

from __future__ import annotations

import re
import secrets
import time

_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"  # Crockford base32, lowercase
_PREFIX_RE = re.compile(r"^[a-z]{2,8}$")
_BODY_LEN = 26


def _encode(value: int, length: int) -> str:
    out: list[str] = []
    for _ in range(length):
        value, rem = divmod(value, 32)
        out.append(_ALPHABET[rem])
    return "".join(reversed(out))


def new_id(prefix: str, *, now_ms: int | None = None) -> str:
    if not _PREFIX_RE.match(prefix):
        raise ValueError(f"invalid id prefix {prefix!r}: use 2-8 lowercase letters")
    ts = now_ms if now_ms is not None else time.time_ns() // 1_000_000
    value = (ts << 80) | secrets.randbits(80)
    return f"{prefix}_{_encode(value, _BODY_LEN)}"


def id_prefix(identifier: str) -> str:
    prefix, sep, body = identifier.partition("_")
    if not sep or len(body) != _BODY_LEN:
        raise ValueError(f"not a Driftless id: {identifier!r}")
    return prefix
