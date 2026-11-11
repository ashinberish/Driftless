"""Migrations apply cleanly and match the ORM models (no drift)."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

import psycopg
import pytest
from alembic import command
from psycopg import sql

from driftless_api.migrate import alembic_config

PG_URL = os.environ.get("DRIFTLESS_TEST_PG_URL")


def _upgrade_check_downgrade(url: str) -> None:
    cfg = alembic_config(url)
    command.upgrade(cfg, "head")
    command.check(cfg)  # raises if models and migrations differ
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


def test_migrations_on_sqlite(tmp_path: Path) -> None:
    _upgrade_check_downgrade(f"sqlite+aiosqlite:///{tmp_path}/m.db")


@pytest.mark.integration
def test_migrations_on_postgres() -> None:
    if not PG_URL:
        pytest.skip("DRIFTLESS_TEST_PG_URL not set")
    name = f"driftless_mig_{secrets.token_hex(4)}"
    drop = sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name))
    with psycopg.connect(PG_URL, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    try:
        _upgrade_check_downgrade(PG_URL.rsplit("/", 1)[0] + f"/{name}")
    finally:
        with psycopg.connect(PG_URL, autocommit=True) as admin:
            admin.execute(drop)
