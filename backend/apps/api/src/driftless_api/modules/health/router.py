from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from driftless_api import __version__

router = APIRouter(tags=["health"])


class Health(BaseModel):
    status: str
    version: str


@router.get("/healthz", response_model=Health, summary="Liveness probe")
async def healthz() -> Health:
    return Health(status="ok", version=__version__)


@router.get("/readyz", response_model=Health, summary="Readiness probe")
async def readyz() -> Health:
    # S1: add metadata-DB and Temporal connectivity checks here.
    return Health(status="ready", version=__version__)
