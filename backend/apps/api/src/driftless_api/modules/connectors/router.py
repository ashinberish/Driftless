"""Supported engines and their capabilities — powers the engine tiles on Connect."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from driftless_connectors import registry
from driftless_connectors.sdk import Capabilities

router = APIRouter(prefix="/connectors", tags=["connectors"])


class ConnectorInfo(BaseModel):
    engine: str
    display_name: str
    default_port: int
    capabilities: Capabilities


@router.get("", response_model=list[ConnectorInfo], summary="List supported engines")
async def list_connectors() -> list[ConnectorInfo]:
    return [
        ConnectorInfo(
            engine=c.engine,
            display_name=c.display_name,
            default_port=c.default_port,
            capabilities=c.capabilities,
        )
        for c in registry.all()
    ]
