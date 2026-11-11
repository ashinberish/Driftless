from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from driftless_api.modules.connections.repository import ConnectionRepository
from driftless_api.modules.connections.schemas import Connection, ConnectionCreate, Page
from driftless_api.modules.connections.service import ConnectionService

router = APIRouter(prefix="/connections", tags=["connections"])


def get_service(request: Request) -> ConnectionService:
    repository: ConnectionRepository = request.app.state.connection_repository
    return ConnectionService(repository)


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


@router.get("/{connection_id}", response_model=Connection, summary="Get a connection")
async def get_connection(connection_id: str, service: Service) -> Connection:
    return await service.get(connection_id)


@router.delete(
    "/{connection_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a connection"
)
async def delete_connection(connection_id: str, service: Service) -> None:
    await service.delete(connection_id)
