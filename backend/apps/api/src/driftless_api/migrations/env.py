"""Alembic environment (async). The URL comes from the Alembic config, which
``driftless_api.migrate`` fills from ``DRIFTLESS_DATABASE_URL``."""

from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy.engine import Connection

# Import models so they register on Base.metadata (autogenerate needs them).
from driftless_api.modules.connections import models as connection_models
from driftless_api.modules.migrations import models as migration_models
from driftless_api.platform.db import Base, Database

MODEL_MODULES = (connection_models, migration_models)

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("set DRIFTLESS_DATABASE_URL (or sqlalchemy.url) to run migrations")
    return url


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def _run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=connection.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    database = Database(_url())
    try:
        async with database.engine.connect() as connection:
            await connection.run_sync(_run)
            await connection.commit()
    finally:
        await database.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
