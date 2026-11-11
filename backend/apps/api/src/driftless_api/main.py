"""Application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from driftless_api import __version__
from driftless_api.modules import connections, connectors, health
from driftless_api.modules.connections.repository import InMemoryConnectionRepository
from driftless_api.platform import (
    REQUEST_ID_HEADER,
    RequestContextMiddleware,
    install_error_handlers,
)
from driftless_api.settings import ApiSettings, get_settings
from driftless_core.logging import configure_logging


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(
        level=settings.log_level, json=settings.log_json, service=settings.service_name
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        # Swap for the SQLAlchemy repository once the metadata DB lands (S1).
        app.state.connection_repository = InMemoryConnectionRepository()
        yield

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
    for module in (connectors, connections):
        app.include_router(module.router, prefix=settings.api_prefix)
    return app


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "driftless_api.main:create_app", factory=True, host=settings.host, port=settings.port
    )
