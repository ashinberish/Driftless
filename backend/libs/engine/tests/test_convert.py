import pytest

from driftless_connectors.mysql import MySQLConnector
from driftless_connectors.postgres import PostgresConnector
from driftless_core.schema import Table
from driftless_engine.convert import DdlGenerator, NamingStyle
from driftless_engine.convert.ddl import to_snake_case


@pytest.mark.parametrize(
    ("raw", "snake"),
    [("InvoiceID", "invoice_id"), ("IssuedAt", "issued_at"), ("already_snake", "already_snake")],
)
def test_snake_case(raw: str, snake: str) -> None:
    assert to_snake_case(raw) == snake


def test_postgres_create_table(invoices: Table) -> None:
    sql = DdlGenerator(PostgresConnector, target_schema="billing").create_table(invoices)
    assert sql.startswith("CREATE TABLE billing.invoices")
    assert "invoice_id INT NOT NULL" in sql
    assert "invoice_no citext" in sql
    assert "amount DECIMAL(19, 4)" in sql
    assert "issued_at TIMESTAMP(6)" in sql  # precision capped at microseconds
    assert "PRIMARY KEY (invoice_id)" in sql


def test_mysql_create_table_from_same_schema(invoices: Table) -> None:
    sql = DdlGenerator(MySQLConnector, target_schema="billing").create_table(invoices)
    assert "IS_VOID TINYINT(1) NOT NULL" in sql.upper().replace("`", "")
    assert "DATETIME(6)" in sql.upper()


def test_preserve_naming_quotes_identifiers(invoices: Table) -> None:
    sql = DdlGenerator(PostgresConnector, naming=NamingStyle.PRESERVE).create_table(invoices)
    assert '"InvoiceID"' in sql


def test_indexes_and_foreign_keys_created_after_copy(invoices: Table) -> None:
    statements = DdlGenerator(PostgresConnector, target_schema="billing").post_copy(invoices)
    assert statements[0] == ("CREATE INDEX ix_invoices_customer ON billing.invoices(customer_id)")
    assert "REFERENCES billing.customers (customer_id)" in statements[1]
