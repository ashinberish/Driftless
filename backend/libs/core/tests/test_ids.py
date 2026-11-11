import pytest

from driftless_core.ids import id_prefix, new_id


def test_new_id_has_prefix_and_fixed_length() -> None:
    value = new_id("mig")
    assert value.startswith("mig_")
    assert len(value) == len("mig_") + 26
    assert id_prefix(value) == "mig"


def test_ids_sort_by_creation_time() -> None:
    earlier = new_id("run", now_ms=1_000)
    later = new_id("run", now_ms=2_000)
    assert earlier < later


@pytest.mark.parametrize("prefix", ["", "X", "toolongprefix", "a1"])
def test_invalid_prefix_rejected(prefix: str) -> None:
    with pytest.raises(ValueError, match="invalid id prefix"):
        new_id(prefix)


def test_id_prefix_rejects_foreign_strings() -> None:
    with pytest.raises(ValueError, match="not a Driftless id"):
        id_prefix("hello")
