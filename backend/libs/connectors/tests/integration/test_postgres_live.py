import pytest

from driftless_connectors.postgres import PostgresConnector
from driftless_connectors.sdk import CheckStatus, ConnectionConfig
from driftless_core.schema import TypeKind

pytestmark = pytest.mark.integration


async def test_checks_report_reachability_access_and_cdc(pg_config: ConnectionConfig) -> None:
    checks = {c.name: c for c in await PostgresConnector(pg_config).check()}
    assert checks["Reachable"].status is CheckStatus.OK
    assert checks["Reachable"].detail is not None
    assert checks["Reachable"].detail.startswith("PostgreSQL")
    assert checks["Read access"].detail == "3 tables visible"
    # Local test clusters may or may not run with wal_level=logical.
    assert checks["Change tracking"].status in {CheckStatus.OK, CheckStatus.WARNING}


async def test_unreachable_server_is_a_failed_check_not_an_exception(
    pg_config: ConnectionConfig,
) -> None:
    bad = pg_config.model_copy(update={"port": 1})
    (check,) = await PostgresConnector(bad).check()
    assert check.name == "Reachable"
    assert check.status is CheckStatus.FAILED


async def test_discover_reads_full_catalog(pg_config: ConnectionConfig) -> None:
    catalog = await PostgresConnector(pg_config).discover()
    assert catalog.engine == "postgres"
    assert catalog.server_version
    names = [t.qualified_name for t in catalog.tables]
    assert names == ["public.audit_raw", "sales.customers", "sales.invoices"]

    customers = catalog.table("sales.customers")
    assert customers.primary_key is not None
    assert customers.primary_key.columns == ("customer_id",)
    assert customers.column("customer_id").identity
    assert customers.column("email").type.length == 255
    assert not customers.column("email").nullable
    created = customers.column("created_at").type
    assert (created.kind, created.precision) == (TypeKind.TIMESTAMP_TZ, 3)
    assert customers.row_estimate == 50

    invoices = catalog.table("sales.invoices")
    (fk,) = invoices.foreign_keys
    assert (fk.ref_schema, fk.ref_table, fk.columns) == ("sales", "customers", ("customer_id",))
    amount = invoices.column("amount").type
    assert (amount.kind, amount.precision, amount.scale) == (TypeKind.DECIMAL, 19, 4)
    tags = invoices.column("tags").type
    assert tags.kind is TypeKind.ARRAY
    assert invoices.column("meta").type.kind is TypeKind.JSON

    assert not catalog.table("public.audit_raw").has_primary_key


async def test_discover_can_be_scoped_to_schemas(pg_config: ConnectionConfig) -> None:
    catalog = await PostgresConnector(pg_config).discover(schemas=["sales"])
    assert {t.schema_name for t in catalog.tables} == {"sales"}
