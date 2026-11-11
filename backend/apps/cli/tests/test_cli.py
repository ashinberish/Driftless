from pathlib import Path

import pytest
from typer.testing import CliRunner

from driftless_cli.main import app
from driftless_core.schema import Catalog, Column, DataType, PrimaryKey, Table, TypeKind

runner = CliRunner()


@pytest.fixture
def catalog_file(tmp_path: Path) -> Path:
    catalog = Catalog(
        engine="mysql",
        tables=(
            Table(
                name="Orders",
                columns=(
                    Column(name="OrderID", type=DataType.of(TypeKind.BIGINT), nullable=False),
                    Column(name="Total", type=DataType.of(TypeKind.DECIMAL, precision=10, scale=2)),
                ),
                primary_key=PrimaryKey(columns=("OrderID",)),
            ),
        ),
    )
    path = tmp_path / "catalog.json"
    path.write_text(catalog.model_dump_json(), encoding="utf-8")
    return path


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "dbm" in result.stdout


def test_connectors_lists_builtins() -> None:
    result = runner.invoke(app, ["connectors"])
    assert result.exit_code == 0
    assert "postgres" in result.stdout


def test_assess_passes_for_ready_catalog(catalog_file: Path) -> None:
    result = runner.invoke(app, ["assess", "-c", str(catalog_file), "-t", "postgres"])
    assert result.exit_code == 0, result.stdout


def test_ddl_renders_postgres(catalog_file: Path) -> None:
    result = runner.invoke(app, ["ddl", "-c", str(catalog_file), "-t", "postgres"])
    assert result.exit_code == 0
    assert "CREATE TABLE orders" in result.stdout
    assert "order_id BIGINT NOT NULL" in result.stdout
