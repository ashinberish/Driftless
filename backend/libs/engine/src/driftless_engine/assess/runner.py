from __future__ import annotations

from collections.abc import Sequence

from driftless_core.schema import Catalog
from driftless_engine.assess.context import AssessContext
from driftless_engine.assess.findings import Assessment, Severity
from driftless_engine.assess.rules import DEFAULT_RULES, Rule
from driftless_engine.assess.scoring import score

_ORDER = {Severity.BLOCKING: 0, Severity.WARNING: 1, Severity.INFO: 2}


def assess(
    catalog: Catalog, target_engine: str, rules: Sequence[Rule] = DEFAULT_RULES
) -> Assessment:
    ctx = AssessContext.build(catalog, target_engine)
    findings = sorted((f for rule in rules for f in rule(ctx)), key=lambda f: _ORDER[f.severity])
    columns = sum(len(t.columns) for t in catalog.tables)
    s = score(
        findings, tables=len(catalog.tables), columns=columns, total_bytes=catalog.total_bytes
    )
    return Assessment(
        source_engine=catalog.engine,
        source_version=catalog.server_version,
        target_engine=target_engine,
        findings=tuple(findings),
        tables=len(catalog.tables),
        columns=columns,
        total_rows=catalog.total_rows,
        total_bytes=catalog.total_bytes,
        score=s.score,
        level=s.level,
        readiness_pct=s.readiness_pct,
        effort_days_min=s.effort_days_min,
        effort_days_max=s.effort_days_max,
    )
