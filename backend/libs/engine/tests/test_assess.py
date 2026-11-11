from driftless_core.schema import Catalog
from driftless_engine.assess import Severity, assess


def test_assessment_orders_findings_by_severity(catalog: Catalog) -> None:
    result = assess(catalog, "postgres")
    severities = [f.severity for f in result.findings]
    assert severities == sorted(
        severities, key=[Severity.BLOCKING, Severity.WARNING, Severity.INFO].index
    )
    assert result.tables == 2
    assert not result.ready


def test_missing_primary_key_is_blocking_and_auto_fixable(catalog: Catalog) -> None:
    result = assess(catalog, "postgres")
    (finding,) = [f for f in result.findings if f.rule_id == "no-primary-key"]
    assert finding.severity is Severity.BLOCKING
    assert finding.objects == ("dbo.audit_raw",)
    assert finding.auto_fixable


def test_unknown_types_reported_with_native_name(catalog: Catalog) -> None:
    result = assess(catalog, "postgres")
    (finding,) = [f for f in result.findings if f.rule_id == "unknown-type"]
    assert "sql_variant" in finding.objects[0]


def test_case_insensitive_rule_only_applies_to_postgres(catalog: Catalog) -> None:
    pg_rules = {f.rule_id for f in assess(catalog, "postgres").findings}
    mysql_rules = {f.rule_id for f in assess(catalog, "mysql").findings}
    assert "case-insensitive-text" in pg_rules
    assert "case-insensitive-text" not in mysql_rules
