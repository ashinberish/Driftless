import itertools
from datetime import datetime
from decimal import Decimal

import pytest

from driftless_core.values import NormalizeOptions
from driftless_engine.copy import plan_integer_chunks
from driftless_engine.validate import checksum_rows, compare


def test_chunks_cover_key_space_without_gaps() -> None:
    chunks = plan_integer_chunks(
        "orders", min_key=1, max_key=1_000, rows=1_000, target_rows_per_chunk=300
    )
    assert len(chunks) == 4
    assert chunks[0].key_range.start is None
    assert chunks[-1].key_range.end is None
    for prev, nxt in itertools.pairwise(chunks):
        assert prev.key_range.end == nxt.key_range.start
    assert chunks[1].id == "orders#1"


def test_empty_table_gets_single_open_chunk() -> None:
    (chunk,) = plan_integer_chunks("empty", min_key=0, max_key=0, rows=0)
    assert chunk.key_range.start is None
    assert chunk.key_range.end is None


def test_invalid_chunk_size_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        plan_integer_chunks("t", min_key=1, max_key=10, rows=10, target_rows_per_chunk=0)


def test_checksum_is_order_independent_and_engine_neutral() -> None:
    sqlserver = [(1, Decimal("10.5000"), True), (2, Decimal("3.0000"), False)]
    postgres = [(2, Decimal("3"), False), (1, Decimal("10.5"), True)]
    result = compare(checksum_rows(sqlserver), checksum_rows(postgres))
    assert result.matches
    assert result.row_difference == 0


def test_checksum_detects_changed_and_duplicate_rows() -> None:
    base = [(1, "a"), (2, "b")]
    assert not compare(checksum_rows(base), checksum_rows([(1, "a"), (2, "B")])).matches
    duplicated = compare(checksum_rows([(1, "a")]), checksum_rows([(1, "a"), (1, "a")]))
    assert not duplicated.matches
    assert duplicated.row_difference == 1


def test_oracle_empty_strings_match_nulls_with_option() -> None:
    opts = NormalizeOptions(empty_string_as_null=True)
    oracle = checksum_rows([(1, None, datetime(2026, 1, 1))], opts)
    postgres = checksum_rows([(1, "", datetime(2026, 1, 1))], opts)
    assert compare(oracle, postgres).matches
