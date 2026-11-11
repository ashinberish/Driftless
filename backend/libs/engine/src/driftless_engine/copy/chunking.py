"""Split a table into primary-key ranges that can be copied (and retried) independently."""

from __future__ import annotations

from dataclasses import dataclass

from driftless_connectors.sdk import KeyRange


@dataclass(frozen=True, slots=True)
class Chunk:
    table: str
    index: int
    key_range: KeyRange

    @property
    def id(self) -> str:
        return f"{self.table}#{self.index}"


def plan_integer_chunks(
    table: str, *, min_key: int, max_key: int, rows: int, target_rows_per_chunk: int = 50_000
) -> list[Chunk]:
    """Evenly split an integer key space ``[min_key, max_key]`` into chunks.

    Ranges are half-open and the last chunk is open-ended, so rows inserted beyond
    ``max_key`` during the copy are still picked up (CDC covers updates).
    """
    if target_rows_per_chunk <= 0:
        raise ValueError("target_rows_per_chunk must be positive")
    if rows <= 0 or max_key < min_key:
        return [Chunk(table=table, index=0, key_range=KeyRange())]

    count = max(1, -(-rows // target_rows_per_chunk))  # ceil division
    span = max_key - min_key + 1
    step = max(1, -(-span // count))
    chunks: list[Chunk] = []
    start = min_key
    index = 0
    while start <= max_key:
        end = start + step
        is_last = end > max_key
        chunks.append(
            Chunk(
                table=table,
                index=index,
                key_range=KeyRange(
                    start=None if index == 0 else (start,),
                    end=None if is_last else (end,),
                ),
            )
        )
        start = end
        index += 1
    return chunks
