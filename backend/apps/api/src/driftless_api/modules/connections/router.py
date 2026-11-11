from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from driftless_api.modules.connections.repository import ConnectionRepository
from driftless_api.modules.connections.schemas import (
    CatalogSummary,
    Connection,
    ConnectionCreate,
    ConnectionSpec,
    ConnectionTestResult,
    Page,
)
from driftless_api.modules.connections.service import ConnectionService

router = APIRouter(prefix="/connections", tags=["connections"])


def get_service(request: Request) -> ConnectionService:
    state = request.app.state
    repository: ConnectionRepository = state.connection_repository
    return ConnectionService(
        repository,
        state.secrets,
        state.connector_factory,
        in_use=state.migration_repository.uses_connection,
    )


Service = Annotated[ConnectionService, Depends(get_service)]


@router.get("", response_model=Page[Connection], summary="List connections")
async def list_connections(service: Service) -> Page[Connection]:
    items = await service.list()
    return Page(items=items, total=len(items))


@router.post(
    "",
    response_model=Connection,
    status_code=status.HTTP_201_CREATED,
    summary="Register a connection",
)
async def create_connection(payload: ConnectionCreate, service: Service) -> Connection:
    return await service.create(payload)


@router.post(
    "/test",
    response_model=ConnectionTestResult,
    summary="Test connection settings before saving",
)
async def test_connection_spec(payload: ConnectionSpec, service: Service) -> ConnectionTestResult:
    return await service.test_spec(payload)


@router.get("/{connection_id}", response_model=Connection, summary="Get a connection")
async def get_connection(connection_id: str, service: Service) -> Connection:
    return await service.get(connection_id)


@router.delete(
    "/{connection_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a connection"
)
async def delete_connection(connection_id: str, service: Service) -> None:
    await service.delete(connection_id)


@router.post(
    "/{connection_id}/test",
    response_model=ConnectionTestResult,
    summary="Run pre-flight checks for a saved connection",
)
async def test_connection(connection_id: str, service: Service) -> ConnectionTestResult:
    return await service.test(connection_id)


@router.post(
    "/{connection_id}/discover",
    response_model=CatalogSummary,
    summary="Read the database catalog (tables, sizes, keys)",
)
async def discover_connection(
    connection_id: str,
    service: Service,
    schemas: Annotated[list[str] | None, Query(description="Limit to these schemas")] = None,
) -> CatalogSummary:
    return await service.discover(connection_id, schemas)
