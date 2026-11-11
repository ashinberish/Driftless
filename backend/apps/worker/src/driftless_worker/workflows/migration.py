"""Migration workflow skeleton.

Stages mirror the product journey (Connect -> Check -> Settings -> Launch -> Copy ->
Go live). S0 wires the assessment stage end to end; later sprints add copy, CDC,
validation and the human-approved cutover signal.
"""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum

from pydantic import BaseModel
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from driftless_worker.activities import AssessInput, AssessOutput


class Stage(StrEnum):
    ASSESSING = "assessing"
    WAITING_FOR_FIXES = "waiting_for_fixes"
    READY = "ready"


class MigrationInput(BaseModel):
    migration_id: str
    assess: AssessInput


class MigrationStatus(BaseModel):
    migration_id: str
    stage: Stage
    assessment: AssessOutput | None = None


_DEFAULT_RETRY = RetryPolicy(initial_interval=timedelta(seconds=2), maximum_attempts=5)


@workflow.defn(name="MigrationWorkflow")
class MigrationWorkflow:
    def __init__(self) -> None:
        self._status: MigrationStatus | None = None

    @workflow.run
    async def run(self, params: MigrationInput) -> MigrationStatus:
        self._status = MigrationStatus(migration_id=params.migration_id, stage=Stage.ASSESSING)
        result = await workflow.execute_activity(
            "assess_catalog",
            params.assess,
            result_type=AssessOutput,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=_DEFAULT_RETRY,
        )
        stage = Stage.READY if result.ready else Stage.WAITING_FOR_FIXES
        self._status = MigrationStatus(
            migration_id=params.migration_id, stage=stage, assessment=result
        )
        return self._status

    @workflow.query(name="status")
    def status(self) -> MigrationStatus | None:
        return self._status
