import uuid
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from driftless_core.values import NULL_TOKEN, NormalizeOptions, normalize, row_digest


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, NULL_TOKEN),
        (True, "t"),
        (False, "f"),
        (42, "42"),
        (Decimal("1.50"), "1.5"),
        (Decimal("0.000"), "0"),
        (1.25, "1.25"),
        (float("nan"), "NaN"),
        (date(2026, 11, 11), "2026-11-11"),
        (b"\x00\xff", "\\x00ff"),
        ({"b": 1, "a": [1, 2]}, '{"a":[1,2],"b":1}'),
    ],
)
def test_normalize_scalars(value: object, expected: str) -> None:
    assert normalize(value) == expected


def test_bool_is_not_rendered_as_int() -> None:
    # bool is a subclass of int — make sure engines storing BIT(1) vs BOOLEAN agree.
    assert normalize(True) != normalize(1)


def test_timezone_aware_timestamps_compare_in_utc() -> None:
    plus_two = timezone(timedelta(hours=2))
    a = datetime(2026, 11, 11, 14, 0, tzinfo=plus_two)
    b = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)
    assert normalize(a) == normalize(b) == "2026-11-11T12:00:00.000000Z"


def test_decimal_scale_option_pads_values() -> None:
    assert normalize(Decimal("1.5"), NormalizeOptions(decimal_scale=4)) == "1.5000"


def test_oracle_empty_string_equals_null() -> None:
    opts = NormalizeOptions(empty_string_as_null=True)
    assert normalize("", opts) == normalize(None, opts)
    assert normalize("") != normalize(None)


def test_separator_in_text_cannot_forge_column_boundaries() -> None:
    assert row_digest(["a\x1fb"]) != row_digest(["a", "b"])


def test_same_row_from_two_engines_has_same_digest() -> None:
    row_id = uuid.uuid4()
    sqlserver_row = [row_id, Decimal("19.9900"), True, datetime(2026, 1, 1, 9, 30)]
    postgres_row = [row_id, Decimal("19.99"), True, datetime(2026, 1, 1, 9, 30)]
    assert row_digest(sqlserver_row) == row_digest(postgres_row)


def test_row_digest_rejects_wrong_option_count() -> None:
    with pytest.raises(ValueError, match="one entry per column"):
        row_digest([1, 2], [NormalizeOptions()])
