"""Assessment rules.

A rule is any callable ``(catalog, target_engine) -> Iterable[Finding]``. Rules are
small and independent so they can be unit-tested one by one and added without touching
the runner. Engine-pair specific rules simply check ``catalog.engine`` / ``target``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence

from driftless_core.schema import Catalog, TypeKind
from driftless_engine.assess.findings import Assessment, Finding, Severity

type Rule = Callable[[Catalog, str], Iterable[Finding]]

# Max identifier length per target engine (bytes/characters, simplified).
_IDENTIFIER_LIMITS = {"postgres": 63, "mysql": 64, "oracle": 128, "sqlserver": 128}


def tables_without_primary_key(catalog: Catalog, _target: str) -> Iterable[Finding]:
    missing = tuple(t.qualified_name for t in catalog.tables if not t.has_primary_key)
    if missing:
        yield Finding(
            rule_id="no-primary-key",
            severity=Severity.BLOCKING,
            title=f"{len(missing)} tables don't have a unique key",
            detail="Without one we can't copy them in parallel or keep them in sync.",
            objects=missing,
            auto_fixable=True,
        )


def unknown_types(catalog: Catalog, _target: str) -> Iterable[Finding]:
    hits = tuple(
        f"{t.qualified_name}.{c.name} ({c.type.native})"
        for t in catalog.tables
        for c in t.columns
        if c.type.kind is TypeKind.UNKNOWN
    )
    if hits:
        yield Finding(
            rule_id="unknown-type",
            severity=Severity.WARNING,
            title=f"{len(hits)} columns use types we don't recognise",
            detail="They will be copied as text unless you choose a mapping.",
            objects=hits,
        )


def identifiers_too_long(catalog: Catalog, target: str) -> Iterable[Finding]:
    limit = _IDENTIFIER_LIMITS.get(target)
    if limit is None:
        return
    names = [t.name for t in catalog.tables] + [c.name for t in catalog.tables for c in t.columns]
    too_long = tuple(sorted({n for n in names if len(n) > limit}))
    if too_long:
        yield Finding(
            rule_id="identifier-too-long",
            severity=Severity.WARNING,
            title=f"{len(too_long)} names are longer than {target} allows ({limit})",
            detail="We'll shorten them deterministically; review the new names.",
            objects=too_long,
            auto_fixable=True,
        )


def case_insensitive_text(catalog: Catalog, target: str) -> Iterable[Finding]:
    if target != "postgres":
        return
    hits = tuple(
        f"{t.qualified_name}.{c.name}"
        for t in catalog.tables
        for c in t.columns
        if c.type.case_insensitive
    )
    if hits:
        yield Finding(
            rule_id="case-insensitive-text",
            severity=Severity.INFO,
            title=f"{len(hits)} columns ignore upper/lowercase today",
            detail="PostgreSQL is case-sensitive by default; we'll keep today's behaviour.",
            objects=hits,
        )


DEFAULT_RULES: tuple[Rule, ...] = (
    tables_without_primary_key,
    unknown_types,
    identifiers_too_long,
    case_insensitive_text,
)


def assess(
    catalog: Catalog, target_engine: str, rules: Sequence[Rule] = DEFAULT_RULES
) -> Assessment:
    findings = tuple(f for rule in rules for f in rule(catalog, target_engine))
    order = {Severity.BLOCKING: 0, Severity.WARNING: 1, Severity.INFO: 2}
    return Assessment(
        source_engine=catalog.engine,
        target_engine=target_engine,
        findings=tuple(sorted(findings, key=lambda f: order[f.severity])),
        tables=len(catalog.tables),
        total_rows=catalog.total_rows,
        total_bytes=catalog.total_bytes,
    )
