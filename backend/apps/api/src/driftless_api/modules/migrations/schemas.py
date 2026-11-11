from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from driftless_engine.assess import Assessment


class MigrationStatus(StrEnum):
    DRAFT = "draft"
    """Created, not assessed yet."""
    READY = "ready"
    """Assessed with no blocking findings."""
    NEEDS_ATTENTION = "needs_attention"
    """Assessed; blocking findings must be resolved."""


class MigrationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"^\S(.*\S)?$")
    source_connection_id: str
    target_engine: str = Field(min_length=1, max_length=32)
    target_connection_id: str | None = None


class Migration(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    source_connection_id: str
    source_engine: str
    target_engine: str
    target_connection_id: str | None
    status: MigrationStatus
    created_at: datetime
    updated_at: datetime


class AssessmentRun(BaseModel):
    """A stored assessment: the engine result plus when it ran."""

    id: str
    migration_id: str
    created_at: datetime
    assessment: Assessment
