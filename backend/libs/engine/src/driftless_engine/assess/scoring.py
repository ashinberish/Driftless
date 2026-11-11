"""Turn findings and catalog size into a complexity score, readiness and effort.

The model is deliberately simple and explainable — every point comes from something
the user can see on the Check screen. Calibrate weights against real migrations.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from driftless_engine.assess.findings import ComplexityLevel, Finding, Severity

_SEVERITY_POINTS = {Severity.BLOCKING: (12, 36), Severity.WARNING: (4, 20), Severity.INFO: (1, 5)}
LOW_MAX = 34
MODERATE_MAX = 69


@dataclass(frozen=True, slots=True)
class Score:
    score: int
    level: ComplexityLevel
    readiness_pct: int
    effort_days_min: int
    effort_days_max: int


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def score(findings: Sequence[Finding], *, tables: int, columns: int, total_bytes: int) -> Score:
    # Size and breadth add effort, but findings dominate: a clean 2 TB database is "low".
    size_pts = _clamp(6 * math.log10(max(total_bytes, 1) / 1e9), 0, 20)  # 1 GB → 0, 1 TB → 18
    table_pts = _clamp(4 * math.log10(max(tables, 1)), 0, 12)  # 1,000 tables → 12
    finding_pts = 0.0
    for severity, (each, cap) in _SEVERITY_POINTS.items():
        count = sum(1 for f in findings if f.severity is severity)
        finding_pts += min(cap, each * count)
    total = round(min(100, size_pts + table_pts + finding_pts))

    level = (
        ComplexityLevel.LOW
        if total <= LOW_MAX
        else ComplexityLevel.MODERATE
        if total <= MODERATE_MAX
        else ComplexityLevel.HIGH
    )

    needs_review = sum(f.affected_columns for f in findings if f.severity is not Severity.INFO)
    readiness = 100 if columns == 0 else round(100 * (1 - min(needs_review, columns) / columns))

    blocking = sum(1 for f in findings if f.severity is Severity.BLOCKING)
    base = 1 + total / 15
    return Score(
        score=total,
        level=level,
        readiness_pct=readiness,
        effort_days_min=round(base),
        effort_days_max=round(base * 1.5) + blocking,
    )
