from __future__ import annotations

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from driftless_api import __version__
from driftless_api.platform.db import Database

router = APIRouter(tags=["health"])


class Health(BaseModel):
    status: str
    version: str
    checks: dict[str, str] = {}


@router.get("/healthz", response_model=Health, summary="Liveness probe")
async def healthz() -> Health:
    return Health(status="ok", version=__version__)


@router.get("/readyz", response_model=Health, summary="Readiness probe")
async def readyz(request: Request, response: Response) -> Health:
    checks: dict[str, str] = {}
    database: Database | None = request.app.state.database
    if database is None:
        checks["database"] = "in-memory"
    else:
        try:
            async with database.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {type(exc).__name__}"
    ready = all(v in {"ok", "in-memory"} for v in checks.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return Health(status="ready" if ready else "not_ready", version=__version__, checks=checks)
