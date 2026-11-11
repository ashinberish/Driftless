from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Severity(StrEnum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


class Finding(BaseModel):
    """One item on the Check screen: plain-language title, affected objects, a fix."""

    model_config = ConfigDict(frozen=True)

    rule_id: str
    severity: Severity
    title: str
    detail: str
    objects: tuple[str, ...] = ()
    auto_fixable: bool = False


class Assessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_engine: str
    target_engine: str
    findings: tuple[Finding, ...]
    tables: int
    total_rows: int
    total_bytes: int

    @property
    def blocking(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is Severity.BLOCKING)

    @property
    def ready(self) -> bool:
        return not self.blocking
