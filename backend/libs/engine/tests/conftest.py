import pytest

from driftless_core.schema import (
    Catalog,
    Column,
    DataType,
    ForeignKey,
    Index,
    PrimaryKey,
    Table,
    TypeKind,
)


@pytest.fixture
def invoices() -> Table:
    return Table(
        schema_name="dbo",
        name="Invoices",
        columns=(
            Column(name="InvoiceID", type=DataType.of(TypeKind.INTEGER), nullable=False),
            Column(name="CustomerID", type=DataType.of(TypeKind.INTEGER), nullable=False),
            Column(
                name="InvoiceNo",
                type=DataType.of(TypeKind.VARCHAR, length=40, case_insensitive=True),
            ),
            Column(name="Amount", type=DataType.of(TypeKind.DECIMAL, precision=19, scale=4)),
            Column(name="IssuedAt", type=DataType.of(TypeKind.TIMESTAMP, precision=7)),
            Column(name="IsVoid", type=DataType.of(TypeKind.BOOLEAN), nullable=False),
        ),
        primary_key=PrimaryKey(columns=("InvoiceID",)),
        foreign_keys=(
            ForeignKey(columns=("CustomerID",), ref_table="Customers", ref_columns=("CustomerID",)),
        ),
        indexes=(Index(name="IX_Invoices_Customer", columns=("CustomerID",)),),
        row_estimate=48_000_000,
        size_bytes=212 * 1024**3,
    )


@pytest.fixture
def catalog(invoices: Table) -> Catalog:
    audit = Table(
        schema_name="dbo",
        name="audit_raw",
        columns=(Column(name="payload", type=DataType.of(TypeKind.UNKNOWN, native="sql_variant")),),
    )
    return Catalog(engine="sqlserver", tables=(invoices, audit))
