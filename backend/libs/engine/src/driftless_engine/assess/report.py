"""Plain-English assessment report (Markdown) for change boards and managers."""

from __future__ import annotations

from driftless_engine.assess.findings import Assessment, Severity

_HEADINGS = {
    Severity.BLOCKING: "Must fix before migrating",
    Severity.WARNING: "Review before migrating",
    Severity.INFO: "For information",
}
_MAX_OBJECTS = 20


def _bytes(n: int) -> str:
    value = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{n} B"  # pragma: no cover


def render_markdown(a: Assessment, *, title: str, generated_at: str) -> str:
    lines = [
        f"# Migration assessment: {title}",
        "",
        f"_{a.source_engine} → {a.target_engine} · generated {generated_at} by Driftless_",
        "",
        "## Summary",
        "",
        "| | |",
        "|---|---|",
        f"| Complexity | **{a.score}/100 ({a.level.value})** |",
        f"| Converts without review | **{a.readiness_pct}%** of {a.columns:,} columns |",
        f"| Estimated effort | **{a.effort_days_min}-{a.effort_days_max} engineer-days** |",
        f"| Scope | {a.tables:,} tables · {a.total_rows:,} rows · {_bytes(a.total_bytes)} |",
        f"| Ready to proceed | {'Yes' if a.ready else 'No — blocking items below'} |",
        "",
    ]
    for severity in Severity:
        items = [f for f in a.findings if f.severity is severity]
        if not items:
            continue
        lines += [f"## {_HEADINGS[severity]} ({len(items)})", ""]
        for f in items:
            lines += [f"### {f.title}", "", f.detail]
            if f.recommendation:
                lines += ["", f"**Recommended:** {f.recommendation}"]
            if f.objects:
                shown = ", ".join(f"`{o}`" for o in f.objects[:_MAX_OBJECTS])
                more = len(f.objects) - _MAX_OBJECTS
                lines += ["", f"Affected: {shown}" + (f" and {more} more" if more > 0 else "")]
            lines.append("")
    if not a.findings:
        lines += ["No issues found.", ""]
    return "\n".join(lines)
