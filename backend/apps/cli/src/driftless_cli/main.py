"""``dbm`` — the Driftless CLI.

Works offline on catalog snapshots (JSON) so assessments and generated DDL can be
reviewed in CI or attached to a change request.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table as RichTable

from driftless_cli import __version__
from driftless_connectors import registry
from driftless_core.schema import Catalog
from driftless_engine.assess import Severity, assess
from driftless_engine.convert import DdlGenerator, NamingStyle

app = typer.Typer(help="Driftless — database migrations with zero drift.", no_args_is_help=True)
console = Console()

CatalogPath = Annotated[
    Path, typer.Option("--catalog", "-c", exists=True, dir_okay=False, help="Catalog JSON")
]
TargetEngine = Annotated[str, typer.Option("--target", "-t", help="Target engine, e.g. postgres")]

_SEVERITY_STYLE = {Severity.BLOCKING: "red", Severity.WARNING: "yellow", Severity.INFO: "cyan"}


def _load(path: Path) -> Catalog:
    return Catalog.model_validate_json(path.read_text(encoding="utf-8"))


@app.command()
def version() -> None:
    """Print the CLI version."""
    console.print(f"dbm {__version__}")


@app.command()
def connectors() -> None:
    """List supported database engines and what they can do."""
    table = RichTable("Engine", "Name", "Read", "Write", "CDC")
    for c in registry.all():
        caps = c.capabilities
        table.add_row(
            c.engine,
            c.display_name,
            *("yes" if v else "-" for v in (caps.read, caps.write, caps.cdc)),
        )
    console.print(table)


@app.command("assess")
def assess_cmd(catalog: CatalogPath, target: TargetEngine) -> None:
    """Assess a catalog snapshot for migration to TARGET. Exit code 1 if blocked."""
    result = assess(_load(catalog), target)
    console.print(
        f"[bold]{result.source_engine} → {result.target_engine}[/]  "
        f"{result.tables} tables · {result.total_rows:,} rows"
    )
    for f in result.findings:
        style = _SEVERITY_STYLE[f.severity]
        console.print(f"  [{style}]{f.severity.value:>8}[/]  {f.title}")
    if not result.ready:
        raise typer.Exit(code=1)


@app.command()
def ddl(
    catalog: CatalogPath,
    target: TargetEngine,
    schema: Annotated[str | None, typer.Option(help="Target schema name")] = None,
    naming: Annotated[NamingStyle, typer.Option(help="Identifier naming")] = NamingStyle.SNAKE_CASE,
) -> None:
    """Print target DDL for every table in the catalog."""
    generator = DdlGenerator(registry.get(target), naming=naming, target_schema=schema)
    for table in _load(catalog).tables:
        typer.echo(generator.create_table(table) + ";")
