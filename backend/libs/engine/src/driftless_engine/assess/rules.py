"""Assessment rules.

A rule is any callable ``(AssessContext) -> Iterable[Finding]``. Rules are small and
independent so they can be unit-tested one by one and added without touching the
runner. Wording is written for the Check screen: plain language first, detail second.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable

from driftless_core.schema import DataType, TypeKind
from driftless_engine.assess.context import AssessContext
from driftless_engine.assess.findings import Category, Finding, Severity

type Rule = Callable[[AssessContext], Iterable[Finding]]

# Max identifier length per target engine (characters, simplified).
_IDENTIFIER_LIMITS = {"postgres": 63, "mysql": 64, "oracle": 128, "sqlserver": 128}

# Kind changes that alter how applications read or query the data.
_STRUCTURAL = {
    TypeKind.ARRAY,
    TypeKind.JSON,
    TypeKind.XML,
    TypeKind.GEOMETRY,
    TypeKind.ENUM,
    TypeKind.UUID,
    TypeKind.TIMESTAMP_TZ,
    TypeKind.INTERVAL,
}

_KIND_ADVICE: dict[tuple[TypeKind, TypeKind], str] = {
    (
        TypeKind.ARRAY,
        TypeKind.JSON,
    ): "Arrays are stored as JSON lists; update queries that index into them.",
    (
        TypeKind.ENUM,
        TypeKind.TEXT,
    ): "Labels are kept as text; we add a CHECK constraint with the allowed values.",
    (TypeKind.UUID, TypeKind.CHAR): "UUIDs are stored as 36-character text.",
    (
        TypeKind.TIMESTAMP_TZ,
        TypeKind.TIMESTAMP,
    ): "Values are converted to UTC; the time zone is not kept.",
    (
        TypeKind.XML,
        TypeKind.TEXT,
    ): "XML is stored as text; XML functions in queries will need changes.",
}


def tables_without_primary_key(ctx: AssessContext) -> Iterable[Finding]:
    missing = [t for t in ctx.catalog.tables if not t.has_primary_key]
    if missing:
        yield Finding(
            rule_id="no-primary-key",
            severity=Severity.BLOCKING,
            category=Category.KEYS,
            title=f"{len(missing)} {_plural(len(missing), "table doesn't", "tables don't")} have a unique key",
            detail="Without one we can't copy them in parallel or keep them in sync.",
            recommendation="Let Driftless add a hidden key column, or choose columns that are unique.",
            objects=tuple(t.qualified_name for t in missing),
            affected_columns=sum(len(t.columns) for t in missing),
            auto_fixable=True,
        )


def unknown_types(ctx: AssessContext) -> Iterable[Finding]:
    hits = [(t, c) for t, c in ctx.columns() if c.type.kind is TypeKind.UNKNOWN]
    if hits:
        yield Finding(
            rule_id="unknown-type",
            severity=Severity.WARNING,
            category=Category.TYPES,
            title=f"{len(hits)} {_plural(len(hits), 'column uses a type', 'columns use types')} we don't recognise",
            detail="They will be copied as text unless you choose a mapping.",
            recommendation="Pick a target type for each in Settings.",
            objects=tuple(f"{t.qualified_name}.{c.name} ({c.type.native})" for t, c in hits),
            affected_columns=len(hits),
        )


def lossy_type_conversions(ctx: AssessContext) -> Iterable[Finding]:
    """Round-trip every column through the target's type mapper and report changes."""
    if ctx.target is None:
        return
    mapper = ctx.target.type_mapper
    groups: dict[tuple[str, str, bool], list[str]] = defaultdict(list)
    for table, column in ctx.columns():
        source = column.type
        if source.kind is TypeKind.UNKNOWN:
            continue  # reported by unknown_types
        landed = mapper.to_canonical(mapper.to_native(source))
        change = _describe_change(source, landed)
        if change is not None:
            before, after, structural = change
            groups[(before, after, structural)].append(f"{table.qualified_name}.{column.name}")

    for (before, after, structural), columns in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        advice = _KIND_ADVICE.get((TypeKind(before.split("(")[0]), TypeKind(after.split("(")[0])))
        yield Finding(
            rule_id="type-conversion",
            severity=Severity.WARNING if structural else Severity.INFO,
            category=Category.TYPES,
            title=f"{len(columns)} {_plural(len(columns), 'column changes', 'columns change')} "
            f"from {before} to {after} in {ctx.target_name}",
            detail=advice
            or (
                "Values keep their meaning; precision beyond what the target supports is rounded."
                if not structural
                else "Applications that depend on the original type may need changes."
            ),
            recommendation="Review the mapping in Settings." if structural else None,
            objects=tuple(columns),
            affected_columns=len(columns) if structural else 0,
        )


def identifiers_too_long(ctx: AssessContext) -> Iterable[Finding]:
    limit = _IDENTIFIER_LIMITS.get(ctx.target_engine)
    if limit is None:
        return
    names = [t.name for t in ctx.catalog.tables] + [c.name for _, c in ctx.columns()]
    too_long = tuple(sorted({n for n in names if len(n) > limit}))
    if too_long:
        yield Finding(
            rule_id="identifier-too-long",
            severity=Severity.WARNING,
            category=Category.NAMING,
            title=f"{len(too_long)} names are longer than {ctx.target_name} allows ({limit})",
            detail="We'll shorten them deterministically and keep a mapping.",
            recommendation="Review the new names in Settings.",
            objects=too_long,
            auto_fixable=True,
        )


def case_insensitive_text(ctx: AssessContext) -> Iterable[Finding]:
    if ctx.target_engine != "postgres":
        return
    hits = [f"{t.qualified_name}.{c.name}" for t, c in ctx.columns() if c.type.case_insensitive]
    if hits:
        yield Finding(
            rule_id="case-insensitive-text",
            severity=Severity.INFO,
            category=Category.BEHAVIOUR,
            title=f"{len(hits)} {_plural(len(hits), 'column ignores', 'columns ignore')} upper/lowercase today",
            detail="PostgreSQL is case-sensitive by default; we'll keep today's behaviour with citext.",
            objects=tuple(hits),
        )


def capability_gaps(ctx: AssessContext) -> Iterable[Finding]:
    if ctx.target is None:
        yield Finding(
            rule_id="unsupported-target",
            severity=Severity.BLOCKING,
            category=Category.CAPABILITY,
            title=f"Driftless has no connector for {ctx.target_engine}",
            detail="Choose a supported target engine.",
        )
        return
    if not ctx.target.capabilities.write:
        yield Finding(
            rule_id="target-not-writable",
            severity=Severity.BLOCKING,
            category=Category.CAPABILITY,
            title=f"Driftless can't write to {ctx.target_name} yet",
            detail=f"Reading from {ctx.target_name} works today; writing to it is on the roadmap.",
            recommendation="Pick another target, or keep this migration as a draft for now.",
        )
    if ctx.source is not None and not ctx.source.capabilities.cdc:
        yield Finding(
            rule_id="no-cdc",
            severity=Severity.WARNING,
            category=Category.CAPABILITY,
            title=f"Zero-downtime isn't available for {ctx.source_name} yet",
            detail="The migration can run offline: the app pauses while data is copied.",
        )


DEFAULT_RULES: tuple[Rule, ...] = (
    capability_gaps,
    tables_without_primary_key,
    unknown_types,
    lossy_type_conversions,
    identifiers_too_long,
    case_insensitive_text,
)


def _describe_change(source: DataType, landed: DataType) -> tuple[str, str, bool] | None:
    if landed.kind is not source.kind:
        return source.kind.value, landed.kind.value, source.kind in _STRUCTURAL
    for attr in ("precision", "scale", "length"):
        before, after = getattr(source, attr), getattr(landed, attr)
        if before is not None and after is not None and after < before:
            return f"{source.kind.value}({before})", f"{landed.kind.value}({after})", False
    return None


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many
