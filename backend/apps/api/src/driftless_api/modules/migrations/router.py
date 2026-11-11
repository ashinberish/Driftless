from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import PlainTextResponse

from driftless_api.modules.connections.router import get_service as get_connection_service
from driftless_api.modules.connections.schemas import Page
from driftless_api.modules.connections.service import ConnectionService
from driftless_api.modules.migrations.schemas import AssessmentRun, Migration, MigrationCreate
from driftless_api.modules.migrations.service import MigrationService

router = APIRouter(prefix="/migrations", tags=["migrations"])


def get_service(
    request: Request,
    connections: Annotated[ConnectionService, Depends(get_connection_service)],
) -> MigrationService:
    return MigrationService(request.app.state.migration_repository, connections)


Service = Annotated[MigrationService, Depends(get_service)]


@router.get("", response_model=Page[Migration], summary="List migrations (newest first)")
async def list_migrations(service: Service) -> Page[Migration]:
    items = await service.list()
    return Page(items=items, total=len(items))


@router.post(
    "", response_model=Migration, status_code=status.HTTP_201_CREATED, summary="Create a draft"
)
async def create_migration(payload: MigrationCreate, service: Service) -> Migration:
    return await service.create(payload)


@router.get("/{migration_id}", response_model=Migration, summary="Get a migration")
async def get_migration(migration_id: str, service: Service) -> Migration:
    return await service.get(migration_id)


@router.post(
    "/{migration_id}/assessments",
    response_model=AssessmentRun,
    status_code=status.HTTP_201_CREATED,
    summary="Assess the source database against the target engine",
)
async def run_assessment(migration_id: str, service: Service) -> AssessmentRun:
    return await service.run_assessment(migration_id)


@router.get(
    "/{migration_id}/assessments/latest",
    response_model=AssessmentRun,
    summary="Most recent assessment",
)
async def latest_assessment(migration_id: str, service: Service) -> AssessmentRun:
    return await service.latest_assessment(migration_id)


@router.get(
    "/{migration_id}/assessments/latest/report.md",
    response_class=PlainTextResponse,
    summary="Download the latest assessment as a Markdown report",
)
async def assessment_report(migration_id: str, service: Service) -> PlainTextResponse:
    body = await service.report_markdown(migration_id)
    return PlainTextResponse(
        body,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="assessment-{migration_id}.md"'},
    )
