"""Fixtures for tests against a real PostgreSQL.

Set ``DRIFTLESS_TEST_PG_URL`` (e.g. ``postgresql://postgres:pw@localhost:5432/postgres``)
to a superuser connection; each test session creates and drops its own database.
"""

from __future__ import annotations

import os
import secrets
from collections.abc import Iterator
from typing import Final
from urllib.parse import urlsplit, urlunsplit

import psycopg
import pytest
from psycopg import sql
from pydantic import SecretStr

from driftless_connectors.sdk import ConnectionConfig, SslMode

PG_URL = os.environ.get("DRIFTLESS_TEST_PG_URL")

SCHEMA_SQL: Final = """
CREATE SCHEMA sales;
CREATE TABLE sales.customers (
    customer_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email varchar(255) NOT NULL,
    created_at timestamp(3) with time zone DEFAULT now()
);
CREATE TABLE sales.invoices (
    invoice_id bigint PRIMARY KEY,
    customer_id integer NOT NULL REFERENCES sales.customers (customer_id),
    amount numeric(19, 4),
    tags text[],
    meta jsonb
);
CREATE TABLE public.audit_raw (payload text);
INSERT INTO sales.customers (email)
    SELECT 'user' || g || '@example.com' FROM generate_series(1, 50) g;
ANALYZE;
"""


@pytest.fixture(scope="session")
def pg_config() -> Iterator[ConnectionConfig]:
    if not PG_URL:
        pytest.skip("DRIFTLESS_TEST_PG_URL not set")
    dbname = f"driftless_it_{secrets.token_hex(4)}"
    with psycopg.connect(PG_URL, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    parts = urlsplit(PG_URL)
    db_url = urlunsplit(parts._replace(path=f"/{dbname}"))
    with psycopg.connect(db_url, autocommit=True) as conn:
        conn.execute(SCHEMA_SQL)
    try:
        yield ConnectionConfig(
            engine="postgres",
            host=parts.hostname or "localhost",
            port=parts.port or 5432,
            database=dbname,
            username=parts.username or "postgres",
            password=SecretStr(parts.password or ""),
            ssl_mode=SslMode.DISABLE,
        )
    finally:
        with psycopg.connect(PG_URL, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(dbname))
            )
