"""Application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from driftless_api import __version__
from driftless_api.modules import connections, connectors, health, migrations
from driftless_api.modules.connections.repository import (
    InMemoryConnectionRepository,
    SqlConnectionRepository,
)
from driftless_api.modules.connections.service import ConnectorFactory
from driftless_api.modules.migrations.repository import (
    InMemoryMigrationRepository,
    SqlMigrationRepository,
)
from driftless_api.platform import (
    REQUEST_ID_HEADER,
    RequestContextMiddleware,
    install_error_handlers,
)
from driftless_api.platform.db import Database
from driftless_api.platform.secrets import build_secret_registry
from driftless_api.settings import ApiSettings, get_settings
from driftless_connectors import registry
from driftless_core.errors import ConfigurationError
from driftless_core.logging import configure_logging
from driftless_core.secrets import SecretResolverRegistry


def create_app(
    settings: ApiSettings | None = None,
    *,
    connector_factory: ConnectorFactory | None = None,
    secrets: SecretResolverRegistry | None = None,
) -> FastAPI:
    """Build the app. Collaborators can be injected for tests; defaults come from settings."""
    settings = settings or get_settings()
    configure_logging(
        level=settings.log_level, json=settings.log_json, service=settings.service_name
    )
    log = structlog.get_logger("api")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.secrets = secrets or build_secret_registry(settings)
        app.state.connector_factory = connector_factory or registry.create
        database: Database | None = None
        if settings.database_url:
            database = Database(settings.database_url)
            app.state.connection_repository = SqlConnectionRepository(database.sessions)
            app.state.migration_repository = SqlMigrationRepository(database.sessions)
        elif settings.is_production:
            raise ConfigurationError("DRIFTLESS_DATABASE_URL is required in production")
        else:
            log.warning("api.in_memory_store", hint="set DRIFTLESS_DATABASE_URL to persist data")
            app.state.connection_repository = InMemoryConnectionRepository()
            app.state.migration_repository = InMemoryMigrationRepository()
        app.state.database = database
        try:
            yield
        finally:
            if database is not None:
                await database.dispose()

    app = FastAPI(
        title="Driftless API",
        version=__version__,
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )
    install_error_handlers(app)

    app.include_router(health.router)
    for module in (connectors, connections, migrations):
        app.include_router(module.router, prefix=settings.api_prefix)
    return app


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "driftless_api.main:create_app", factory=True, host=settings.host, port=settings.port
    )
