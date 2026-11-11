import pytest
from pydantic import ValidationError

from driftless_core.schema import Catalog, Column, DataType, PrimaryKey, Table, TypeKind


def test_datatype_string_form() -> None:
    assert str(DataType.of(TypeKind.DECIMAL, precision=19, scale=4)) == "decimal(19, 4)"
    assert str(DataType.of(TypeKind.VARCHAR, length=40, case_insensitive=True)) == "varchar(40) ci"
    arr = DataType.of(TypeKind.ARRAY, element=DataType.of(TypeKind.INTEGER))
    assert str(arr) == "integer[]"


@pytest.mark.parametrize(
    "params",
    [
        {"kind": TypeKind.INTEGER, "length": 10},
        {"kind": TypeKind.VARCHAR, "scale": 2},
        {"kind": TypeKind.ARRAY},
        {"kind": TypeKind.ENUM},
    ],
)
def test_datatype_rejects_invalid_params(params: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        DataType.model_validate(params)


def test_table_helpers() -> None:
    table = Table(
        schema_name="dbo",
        name="invoices",
        columns=(Column(name="id", type=DataType.of(TypeKind.INTEGER), nullable=False),),
        primary_key=PrimaryKey(columns=("id",)),
        row_estimate=10,
        size_bytes=2048,
    )
    assert table.qualified_name == "dbo.invoices"
    assert table.has_primary_key
    assert table.column("id").type.kind is TypeKind.INTEGER
    with pytest.raises(KeyError):
        table.column("missing")

    catalog = Catalog(engine="sqlserver", tables=(table,))
    assert catalog.table("dbo.invoices") is table
    assert catalog.total_rows == 10
    assert catalog.total_bytes == 2048


def test_models_are_immutable() -> None:
    col = Column(name="id", type=DataType.of(TypeKind.INTEGER))
    with pytest.raises(ValidationError):
        col.name = "other"  # type: ignore[misc]
