"""Order-independent chunk checksums over normalized rows.

Each row is hashed from its *normalized* values (see ``driftless_core.values``), then
row hashes are combined with XOR-free modular addition so the result does not depend on
the order rows were read in — engines sort collated text differently.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from driftless_core.values import NORMALIZATION_VERSION, NormalizeOptions, row_digest

_MOD = 1 << 256


@dataclass(frozen=True, slots=True)
class ChunkChecksum:
    rows: int
    digest: str
    version: int = NORMALIZATION_VERSION


@dataclass(frozen=True, slots=True)
class ChunkComparison:
    source: ChunkChecksum
    target: ChunkChecksum

    @property
    def matches(self) -> bool:
        return self.source == self.target

    @property
    def row_difference(self) -> int:
        return self.target.rows - self.source.rows


def checksum_rows(
    rows: Iterable[Sequence[object]],
    options: Sequence[NormalizeOptions] | NormalizeOptions | None = None,
) -> ChunkChecksum:
    total = 0
    count = 0
    for row in rows:
        # Addition (not XOR) so duplicate rows don't cancel each other out.
        total = (total + int.from_bytes(row_digest(row, options), "big")) % _MOD
        count += 1
    return ChunkChecksum(rows=count, digest=f"{total:064x}")


def compare(source: ChunkChecksum, target: ChunkChecksum) -> ChunkComparison:
    if source.version != target.version:
        raise ValueError("checksums were produced with different normalization versions")
    return ChunkComparison(source=source, target=target)
