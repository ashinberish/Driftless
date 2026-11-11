"""Migration drafts and assessments.

S2 runs the assessment synchronously (catalog analysis takes seconds). When copy
workflows arrive (S4) the same service call starts a Temporal workflow instead.
"""

from __future__ import annotations

from datetime import UTC, datetime

from driftless_api.modules.connections.service import ConnectionService
from driftless_api.modules.migrations.repository import MigrationRepository
from driftless_api.modules.migrations.schemas import (
    AssessmentRun,
    Migration,
    MigrationCreate,
    MigrationStatus,
)
from driftless_connectors import registry
from driftless_core.errors import ConfigurationError, ConflictError, NotFoundError
from driftless_core.ids import new_id
from driftless_engine.assess import assess, render_markdown


class MigrationService:
    def __init__(self, repository: MigrationRepository, connections: ConnectionService) -> None:
        self._repo = repository
        self._connections = connections

    async def create(self, payload: MigrationCreate) -> Migration:
        registry.get(payload.target_engine)  # NotFoundError for unknown engines
        source = await self._connections.get(payload.source_connection_id)
        if payload.target_connection_id is not None:
            target = await self._connections.get(payload.target_connection_id)
            if target.engine != payload.target_engine:
                raise ConfigurationError(
                    f"target connection is {target.engine}, not {payload.target_engine}",
                    details={"target_connection_id": target.id},
                )
            if target.id == source.id:
                raise ConflictError("source and target must be different connections")
        now = datetime.now(UTC)
        migration = Migration(
            id=new_id("mig"),
            name=payload.name,
            source_connection_id=source.id,
            source_engine=source.engine,
            target_engine=payload.target_engine,
            target_connection_id=payload.target_connection_id,
            status=MigrationStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )
        await self._repo.add(migration)
        return migration

    async def get(self, migration_id: str) -> Migration:
        migration = await self._repo.get(migration_id)
        if migration is None:
            raise NotFoundError(f"migration {migration_id!r} not found")
        return migration

    async def list(self) -> list[Migration]:
        return await self._repo.list()

    async def run_assessment(self, migration_id: str) -> AssessmentRun:
        migration = await self.get(migration_id)
        catalog = await self._connections.catalog(migration.source_connection_id)
        result = assess(catalog, migration.target_engine)
        now = datetime.now(UTC)
        run = AssessmentRun(
            id=new_id("asmt"), migration_id=migration.id, created_at=now, assessment=result
        )
        await self._repo.add_assessment(run)
        status = MigrationStatus.READY if result.ready else MigrationStatus.NEEDS_ATTENTION
        await self._repo.set_status(migration.id, status, now)
        return run

    async def latest_assessment(self, migration_id: str) -> AssessmentRun:
        await self.get(migration_id)
        run = await self._repo.latest_assessment(migration_id)
        if run is None:
            raise NotFoundError(f"migration {migration_id!r} has not been assessed yet")
        return run

    async def report_markdown(self, migration_id: str) -> str:
        migration = await self.get(migration_id)
        run = await self.latest_assessment(migration_id)
        return render_markdown(
            run.assessment,
            title=migration.name,
            generated_at=run.created_at.strftime("%Y-%m-%d %H:%M UTC"),
        )
