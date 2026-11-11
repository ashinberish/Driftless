from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, computed_field


class Severity(StrEnum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


class Category(StrEnum):
    KEYS = "keys"
    TYPES = "types"
    NAMING = "naming"
    BEHAVIOUR = "behaviour"
    CAPABILITY = "capability"


class ComplexityLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class Finding(BaseModel):
    """One item on the Check screen: plain-language title, affected objects, a fix."""

    model_config = ConfigDict(frozen=True)

    rule_id: str
    severity: Severity
    category: Category
    title: str
    detail: str
    recommendation: str | None = None
    objects: tuple[str, ...] = ()
    affected_columns: int = 0
    auto_fixable: bool = False


class Assessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_engine: str
    source_version: str | None = None
    target_engine: str
    findings: tuple[Finding, ...]
    tables: int
    columns: int
    total_rows: int
    total_bytes: int
    score: int
    level: ComplexityLevel
    readiness_pct: int
    """Share of columns that convert without anyone needing to review them."""
    effort_days_min: int
    effort_days_max: int

    @property
    def blocking(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is Severity.BLOCKING)

    @computed_field  # serialized, so API clients get it too
    @property
    def ready(self) -> bool:
        return not self.blocking
