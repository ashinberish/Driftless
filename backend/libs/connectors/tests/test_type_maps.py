import pytest

from driftless_connectors.mysql import MySQLTypeMapper
from driftless_connectors.postgres import PostgresTypeMapper
from driftless_connectors.sdk import TypeMapper, parse_native
from driftless_core.schema import DataType, TypeKind

pg = PostgresTypeMapper()
my = MySQLTypeMapper()


def test_mappers_satisfy_protocol() -> None:
    assert isinstance(pg, TypeMapper)
    assert isinstance(my, TypeMapper)


@pytest.mark.parametrize(
    ("declaration", "base", "args", "suffix"),
    [
        ("numeric(19, 4)", "numeric", ("19", "4"), ""),
        ("timestamp(3) with time zone", "timestamp", ("3",), "with time zone"),
        ("timestamp with time zone", "timestamp with time zone", (), ""),
        ("character varying(40)", "character varying", ("40",), ""),
        ("int(10) unsigned", "int", ("10",), "unsigned"),
        ("enum('a,b','c')", "enum", ("'a,b'", "'c'"), ""),
    ],
)
def test_parse_native(declaration: str, base: str, args: tuple[str, ...], suffix: str) -> None:
    parsed = parse_native(declaration)
    assert (parsed.base, parsed.args, parsed.suffix) == (base, args, suffix)


@pytest.mark.parametrize(
    ("native", "kind", "params"),
    [
        ("integer", TypeKind.INTEGER, {}),
        ("numeric(19,4)", TypeKind.DECIMAL, {"precision": 19, "scale": 4}),
        ("character varying(40)", TypeKind.VARCHAR, {"length": 40}),
        ("timestamp(3) with time zone", TypeKind.TIMESTAMP_TZ, {"precision": 3}),
        ("timestamp without time zone", TypeKind.TIMESTAMP, {}),
        ("citext", TypeKind.TEXT, {"case_insensitive": True}),
        ("jsonb", TypeKind.JSON, {}),
        ("some_custom_domain", TypeKind.UNKNOWN, {}),
    ],
)
def test_postgres_to_canonical(native: str, kind: TypeKind, params: dict[str, object]) -> None:
    dt = pg.to_canonical(native)
    assert dt.kind is kind
    for key, value in params.items():
        assert getattr(dt, key) == value
    assert dt.native == native


def test_postgres_arrays() -> None:
    dt = pg.to_canonical("integer[]")
    assert dt.kind is TypeKind.ARRAY
    assert dt.element is not None
    assert dt.element.kind is TypeKind.INTEGER
    assert pg.to_native(dt) == "integer[]"


@pytest.mark.parametrize(
    ("native", "kind"),
    [
        ("tinyint(1)", TypeKind.BOOLEAN),
        ("tinyint(4)", TypeKind.SMALLINT),
        ("int(10) unsigned", TypeKind.BIGINT),
        ("bigint unsigned", TypeKind.DECIMAL),
        ("datetime(6)", TypeKind.TIMESTAMP),
        ("timestamp", TypeKind.TIMESTAMP_TZ),
        ("longtext", TypeKind.TEXT),
        ("enum('draft','live')", TypeKind.ENUM),
    ],
)
def test_mysql_to_canonical(native: str, kind: TypeKind) -> None:
    assert my.to_canonical(native).kind is kind


def test_mysql_enum_labels_preserved() -> None:
    dt = my.to_canonical("enum('draft','live')")
    assert dt.enum_values == ("draft", "live")
    assert my.to_native(dt) == "enum('draft','live')"


@pytest.mark.parametrize(
    ("dt", "pg_native", "mysql_native"),
    [
        (DataType.of(TypeKind.BOOLEAN), "boolean", "tinyint(1)"),
        (DataType.of(TypeKind.DECIMAL, precision=19, scale=4), "numeric(19,4)", "decimal(19,4)"),
        (DataType.of(TypeKind.VARCHAR, length=40), "varchar(40)", "varchar(40)"),
        (DataType.of(TypeKind.TIMESTAMP, precision=7), "timestamp(6)", "datetime(6)"),
        (DataType.of(TypeKind.UUID), "uuid", "char(36)"),
        (DataType.of(TypeKind.JSON), "jsonb", "json"),
    ],
)
def test_cross_engine_rendering(dt: DataType, pg_native: str, mysql_native: str) -> None:
    """The same canonical type renders correctly for each target engine."""
    assert pg.to_native(dt) == pg_native
    assert my.to_native(dt) == mysql_native


def test_mysql_to_postgres_roundtrip_via_canonical() -> None:
    for native in ["int", "varchar(255)", "decimal(10,2)", "datetime(3)", "json", "tinyint(1)"]:
        canonical = my.to_canonical(native)
        rendered = pg.to_native(canonical)
        assert pg.to_canonical(rendered).kind is canonical.kind, native


def test_postgres_version_is_shortened() -> None:
    from driftless_connectors.postgres.connector import _short_version  # pyright: ignore[reportPrivateUsage]

    assert _short_version("16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)") == "16.15"
    assert _short_version("17.2") == "17.2"
    assert _short_version(None) is None
