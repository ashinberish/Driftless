"""Assessment activities."""

from __future__ import annotations

from pydantic import BaseModel
from temporalio import activity

from driftless_core.schema import Catalog
from driftless_engine.assess import assess


class AssessInput(BaseModel):
    catalog: Catalog
    target_engine: str


class AssessOutput(BaseModel):
    ready: bool
    blocking: int
    findings: int


@activity.defn(name="assess_catalog")
async def assess_catalog(params: AssessInput) -> AssessOutput:
    result = assess(params.catalog, params.target_engine)
    return AssessOutput(
        ready=result.ready, blocking=len(result.blocking), findings=len(result.findings)
    )
