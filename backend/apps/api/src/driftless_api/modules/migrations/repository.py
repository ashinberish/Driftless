"""Persistence port for migrations + in-memory and SQL adapters (same contract)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from driftless_api.modules.migrations.models import AssessmentRecord, MigrationRecord
from driftless_api.modules.migrations.schemas import AssessmentRun, Migration, MigrationStatus
from driftless_core.errors import ConflictError, NotFoundError
from driftless_engine.assess import Assessment


class MigrationRepository(Protocol):
    async def add(self, migration: Migration) -> None: ...
    async def get(self, migration_id: str) -> Migration | None: ...
    async def list(self) -> list[Migration]: ...
    async def set_status(
        self, migration_id: str, status: MigrationStatus, at: datetime
    ) -> None: ...
    async def add_assessment(self, run: AssessmentRun) -> None: ...
    async def latest_assessment(self, migration_id: str) -> AssessmentRun | None: ...
    async def uses_connection(self, connection_id: str) -> bool: ...


def _duplicate(name: str) -> ConflictError:
    return ConflictError(f"a migration named {name!r} already exists", details={"name": name})


class InMemoryMigrationRepository:
    def __init__(self) -> None:
        self._items: dict[str, Migration] = {}
        self._runs: dict[str, list[AssessmentRun]] = {}

    async def add(self, migration: Migration) -> None:
        if any(m.name == migration.name for m in self._items.values()):
            raise _duplicate(migration.name)
        self._items[migration.id] = migration

    async def get(self, migration_id: str) -> Migration | None:
        return self._items.get(migration_id)

    async def list(self) -> list[Migration]:
        return sorted(self._items.values(), key=lambda m: (m.created_at, m.id), reverse=True)

    async def set_status(self, migration_id: str, status: MigrationStatus, at: datetime) -> None:
        current = self._items.get(migration_id)
        if current is None:
            raise NotFoundError(f"migration {migration_id!r} not found")
        self._items[migration_id] = current.model_copy(update={"status": status, "updated_at": at})

    async def add_assessment(self, run: AssessmentRun) -> None:
        self._runs.setdefault(run.migration_id, []).append(run)

    async def latest_assessment(self, migration_id: str) -> AssessmentRun | None:
        runs = self._runs.get(migration_id)
        return max(runs, key=lambda r: (r.created_at, r.id)) if runs else None

    async def uses_connection(self, connection_id: str) -> bool:
        return any(
            connection_id in (m.source_connection_id, m.target_connection_id)
            for m in self._items.values()
        )


class SqlMigrationRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def add(self, migration: Migration) -> None:
        async with self._sessions.begin() as session:
            session.add(MigrationRecord(**migration.model_dump(mode="python")))
            try:
                await session.flush()
            except IntegrityError as exc:
                raise _duplicate(migration.name) from exc

    async def get(self, migration_id: str) -> Migration | None:
        async with self._sessions() as session:
            record = await session.get(MigrationRecord, migration_id)
            return Migration.model_validate(record) if record else None

    async def list(self) -> list[Migration]:
        async with self._sessions() as session:
            result = await session.scalars(
                select(MigrationRecord).order_by(
                    MigrationRecord.created_at.desc(), MigrationRecord.id.desc()
                )
            )
            return [Migration.model_validate(r) for r in result]

    async def set_status(self, migration_id: str, status: MigrationStatus, at: datetime) -> None:
        async with self._sessions.begin() as session:
            await session.execute(
                update(MigrationRecord)
                .where(MigrationRecord.id == migration_id)
                .values(status=status.value, updated_at=at)
            )

    async def add_assessment(self, run: AssessmentRun) -> None:
        async with self._sessions.begin() as session:
            session.add(
                AssessmentRecord(
                    id=run.id,
                    migration_id=run.migration_id,
                    created_at=run.created_at,
                    result=run.assessment.model_dump(mode="json"),
                )
            )

    async def latest_assessment(self, migration_id: str) -> AssessmentRun | None:
        async with self._sessions() as session:
            record = await session.scalar(
                select(AssessmentRecord)
                .where(AssessmentRecord.migration_id == migration_id)
                .order_by(AssessmentRecord.created_at.desc(), AssessmentRecord.id.desc())
                .limit(1)
            )
            if record is None:
                return None
            return AssessmentRun(
                id=record.id,
                migration_id=record.migration_id,
                created_at=record.created_at,
                assessment=Assessment.model_validate(record.result),
            )

    async def uses_connection(self, connection_id: str) -> bool:
        async with self._sessions() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(MigrationRecord)
                .where(
                    or_(
                        MigrationRecord.source_connection_id == connection_id,
                        MigrationRecord.target_connection_id == connection_id,
                    )
                )
            )
            return bool(count)
