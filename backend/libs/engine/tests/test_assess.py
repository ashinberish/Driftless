import pytest

from driftless_core.schema import Catalog, Column, DataType, PrimaryKey, Table, TypeKind
from driftless_engine.assess import (
    AssessContext,
    Category,
    ComplexityLevel,
    Finding,
    Severity,
    assess,
    render_markdown,
)
from driftless_engine.assess.rules import capability_gaps, lossy_type_conversions
from driftless_engine.assess.scoring import score


def _table(name: str, *cols: tuple[str, DataType], pk: bool = True) -> Table:
    columns = tuple(Column(name=n, type=t) for n, t in cols)
    return Table(
        schema_name="app",
        name=name,
        columns=columns,
        primary_key=PrimaryKey(columns=(columns[0].name,)) if pk else None,
        row_estimate=1000,
        size_bytes=10_000_000,
    )


def _by_rule(findings: tuple[Finding, ...], rule_id: str) -> list[Finding]:
    return [f for f in findings if f.rule_id == rule_id]


# --------------------------------------------------------------------------- runner
def test_assessment_orders_findings_by_severity(catalog: Catalog) -> None:
    result = assess(catalog, "postgres")
    order = [Severity.BLOCKING, Severity.WARNING, Severity.INFO]
    severities = [f.severity for f in result.findings]
    assert severities == sorted(severities, key=order.index)
    assert result.tables == 2
    assert result.columns == 7
    assert not result.ready


def test_missing_primary_key_is_blocking_and_auto_fixable(catalog: Catalog) -> None:
    (finding,) = _by_rule(assess(catalog, "postgres").findings, "no-primary-key")
    assert finding.severity is Severity.BLOCKING
    assert finding.category is Category.KEYS
    assert finding.objects == ("dbo.audit_raw",)
    assert finding.auto_fixable
    assert finding.title == "1 table doesn't have a unique key"


def test_unknown_types_reported_with_native_name(catalog: Catalog) -> None:
    (finding,) = _by_rule(assess(catalog, "postgres").findings, "unknown-type")
    assert "sql_variant" in finding.objects[0]


def test_case_insensitive_rule_only_applies_to_postgres(catalog: Catalog) -> None:
    pg_rules = {f.rule_id for f in assess(catalog, "postgres").findings}
    mysql_rules = {f.rule_id for f in assess(catalog, "mysql").findings}
    assert "case-insensitive-text" in pg_rules
    assert "case-insensitive-text" not in mysql_rules


# ------------------------------------------------------------------ type conversions
def test_lossy_conversions_to_mysql_are_grouped_and_explained() -> None:
    catalog = Catalog(
        engine="postgres",
        tables=(
            _table(
                "events",
                ("id", DataType.of(TypeKind.UUID)),
                ("tags", DataType.of(TypeKind.ARRAY, element=DataType.of(TypeKind.TEXT))),
                ("labels", DataType.of(TypeKind.ARRAY, element=DataType.of(TypeKind.TEXT))),
                ("at", DataType.of(TypeKind.TIMESTAMP_TZ, precision=6)),
                ("name", DataType.of(TypeKind.TEXT)),
            ),
        ),
    )
    findings = list(lossy_type_conversions(AssessContext.build(catalog, "mysql")))
    titles = [f.title for f in findings]
    assert titles[0] == "2 columns change from array to json in MySQL"  # largest group first
    assert all(f.severity is Severity.WARNING for f in findings)
    arrays = findings[0]
    assert arrays.objects == ("app.events.tags", "app.events.labels")
    assert "JSON lists" in arrays.detail
    assert any("timestamp_tz to timestamp" in t for t in titles)
    assert any("uuid to char" in t for t in titles)
    assert not any("text" in t for t in titles)  # unchanged columns aren't reported


def test_precision_loss_is_informational() -> None:
    catalog = Catalog(
        engine="sqlserver",
        tables=(_table("t", ("id", DataType.of(TypeKind.TIMESTAMP, precision=7))),),
    )
    (finding,) = lossy_type_conversions(AssessContext.build(catalog, "postgres"))
    assert finding.severity is Severity.INFO
    assert finding.title == "1 column changes from timestamp(7) to timestamp(6) in PostgreSQL"
    assert finding.affected_columns == 0  # rounding doesn't need a human


def test_same_engine_migration_has_no_conversion_findings() -> None:
    catalog = Catalog(
        engine="postgres",
        tables=(
            _table(
                "t",
                ("id", DataType.of(TypeKind.BIGINT)),
                ("doc", DataType.of(TypeKind.JSON)),
                ("amount", DataType.of(TypeKind.DECIMAL, precision=19, scale=4)),
            ),
        ),
    )
    assert list(lossy_type_conversions(AssessContext.build(catalog, "postgres"))) == []


# --------------------------------------------------------------------- capabilities
def test_target_without_write_support_blocks() -> None:
    catalog = Catalog(engine="postgres", tables=())
    (finding,) = capability_gaps(AssessContext.build(catalog, "mysql"))
    assert finding.rule_id == "target-not-writable"
    assert finding.severity is Severity.BLOCKING


def test_source_without_cdc_warns_offline_only() -> None:
    catalog = Catalog(engine="mysql", tables=())
    rules = {f.rule_id: f for f in capability_gaps(AssessContext.build(catalog, "postgres"))}
    assert rules["no-cdc"].severity is Severity.WARNING


def test_unknown_target_engine_blocks() -> None:
    catalog = Catalog(engine="postgres", tables=())
    (finding,) = capability_gaps(AssessContext.build(catalog, "db2"))
    assert finding.rule_id == "unsupported-target"


# -------------------------------------------------------------------------- scoring
def test_small_clean_database_is_low_complexity() -> None:
    s = score([], tables=10, columns=50, total_bytes=50_000_000)
    assert s.level is ComplexityLevel.LOW
    assert s.readiness_pct == 100
    assert 1 <= s.effort_days_min <= s.effort_days_max


@pytest.mark.parametrize(
    ("blocking", "warnings", "level"),
    [(0, 0, ComplexityLevel.LOW), (2, 3, ComplexityLevel.MODERATE), (3, 5, ComplexityLevel.HIGH)],
)
def test_findings_raise_complexity(blocking: int, warnings: int, level: ComplexityLevel) -> None:
    def f(sev: Severity) -> Finding:
        return Finding(rule_id="x", severity=sev, category=Category.TYPES, title="t", detail="d")

    findings = [f(Severity.BLOCKING)] * blocking + [f(Severity.WARNING)] * warnings
    assert score(findings, tables=200, columns=2000, total_bytes=2 * 1024**4).level is level


def test_blocking_findings_are_never_low_complexity() -> None:
    blocker = Finding(
        rule_id="x", severity=Severity.BLOCKING, category=Category.KEYS, title="t", detail="d"
    )
    assert (
        score([blocker], tables=2, columns=4, total_bytes=1_000).level is ComplexityLevel.MODERATE
    )


def test_readiness_counts_columns_needing_review() -> None:
    finding = Finding(
        rule_id="x",
        severity=Severity.WARNING,
        category=Category.TYPES,
        title="t",
        detail="d",
        affected_columns=25,
    )
    assert score([finding], tables=1, columns=100, total_bytes=1).readiness_pct == 75


# --------------------------------------------------------------------------- report
def test_markdown_report_has_summary_and_sections(catalog: Catalog) -> None:
    report = render_markdown(
        assess(catalog, "postgres"), title="billing-db", generated_at="2026-12-14 10:00 UTC"
    )
    assert report.startswith("# Migration assessment: billing-db")
    assert "| Ready to proceed | No — blocking items below |" in report
    assert "## Must fix before migrating (1)" in report
    assert "`dbo.audit_raw`" in report
