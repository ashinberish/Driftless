from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from driftless_api.main import create_app
from driftless_api.migrate import alembic_config
from driftless_api.settings import ApiSettings
from driftless_core.config import Environment
from driftless_core.errors import ConfigurationError
from driftless_core.secrets import EnvSecretResolver, SecretResolverRegistry

PREFIX = "/api/v1"


def _secrets() -> SecretResolverRegistry:
    return SecretResolverRegistry([EnvSecretResolver({"BILLING_PW": "s3cret"})])


@pytest.fixture
def client(fake_connector: Any) -> Iterator[TestClient]:
    app = create_app(
        ApiSettings(environment=Environment.TEST, log_level="WARNING"),
        connector_factory=fake_connector,
        secrets=_secrets(),
    )
    with TestClient(app) as c:
        yield c


def _payload(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "name": "billing-prod",
        "engine": "postgres",
        "host": "billing-prod-01.internal",
        "port": 5432,
        "database": "billing",
        "username": "driftless_ro",
        "secret_ref": "env:BILLING_PW",
    }
    body.update(overrides)
    return body


def _create(client: TestClient, **overrides: object) -> dict[str, object]:
    res = client.post(f"{PREFIX}/connections", json=_payload(**overrides))
    assert res.status_code == 201, res.text
    return res.json()


# ------------------------------------------------------------------ platform
def test_health_and_request_id(client: TestClient) -> None:
    res = client.get("/healthz", headers={"X-Request-ID": "req-test"})
    assert res.status_code == 200
    assert res.headers["X-Request-ID"] == "req-test"


def test_readyz_reports_store(client: TestClient) -> None:
    assert client.get("/readyz").json()["checks"] == {"database": "in-memory"}


def test_production_requires_database() -> None:
    app = create_app(ApiSettings(environment=Environment.PRODUCTION, log_level="WARNING"))
    with pytest.raises(ConfigurationError, match="DATABASE_URL"), TestClient(app):
        pass


def test_list_connectors(client: TestClient) -> None:
    engines = {c["engine"] for c in client.get(f"{PREFIX}/connectors").json()}
    assert {"postgres", "mysql"} <= engines


# ---------------------------------------------------------------- connections
def test_connection_crud(client: TestClient) -> None:
    conn = _create(client)
    assert str(conn["id"]).startswith("conn_")
    assert "password" not in conn
    assert client.get(f"{PREFIX}/connections").json()["total"] == 1
    assert client.get(f"{PREFIX}/connections/{conn['id']}").json()["name"] == "billing-prod"
    assert client.delete(f"{PREFIX}/connections/{conn['id']}").status_code == 204
    missing = client.get(f"{PREFIX}/connections/{conn['id']}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_duplicate_name_conflicts(client: TestClient) -> None:
    _create(client)
    res = client.post(f"{PREFIX}/connections", json=_payload())
    assert res.status_code == 409


@pytest.mark.parametrize(
    ("overrides", "status"),
    [
        ({"engine": "db2"}, 404),
        ({"secret_ref": "hunter2"}, 422),  # plaintext password, not a reference
        ({"secret_ref": "vault:db/billing"}, 400),  # backend not configured here
        ({"port": 70000}, 422),
        ({"name": "  "}, 422),
    ],
)
def test_invalid_connections_rejected(
    client: TestClient, overrides: dict[str, object], status: int
) -> None:
    assert client.post(f"{PREFIX}/connections", json=_payload(**overrides)).status_code == status


def test_test_unsaved_spec_resolves_secret_at_connect_time(
    client: TestClient, fake_connector: Any
) -> None:
    spec = _payload()
    spec.pop("name")
    res = client.post(f"{PREFIX}/connections/test", json=spec)
    body = res.json()
    assert res.status_code == 200
    assert body["ok"] is True  # warnings don't fail the test
    assert [c["name"] for c in body["checks"]] == ["Reachable", "Change tracking"]
    (config,) = fake_connector.seen
    assert config.password is not None
    assert config.password.get_secret_value() == "s3cret"


def test_failed_check_makes_result_not_ok(client: TestClient) -> None:
    conn = _create(client, host="unreachable")
    body = client.post(f"{PREFIX}/connections/{conn['id']}/test").json()
    assert body["ok"] is False
    assert body["checks"][0]["status"] == "failed"


def test_missing_secret_is_reported_as_a_check(client: TestClient) -> None:
    spec = _payload(secret_ref="env:NOT_SET")
    spec.pop("name")
    body = client.post(f"{PREFIX}/connections/test", json=spec).json()
    assert body["ok"] is False
    assert body["checks"][0]["name"] == "Credentials"


def test_discover_summarizes_catalog_largest_first(client: TestClient) -> None:
    conn = _create(client)
    body = client.post(f"{PREFIX}/connections/{conn['id']}/discover").json()
    assert body["total_tables"] == 2
    assert body["schemas"] == ["public", "sales"]
    assert [t["name"] for t in body["tables"]] == ["sales.orders", "public.audit_raw"]
    assert body["tables"][1]["has_primary_key"] is False

    scoped = client.post(f"{PREFIX}/connections/{conn['id']}/discover?schemas=sales").json()
    assert scoped["total_tables"] == 1


def test_connections_persist_in_metadata_db(tmp_path: Path, fake_connector: Any) -> None:
    from alembic import command

    url = f"sqlite+aiosqlite:///{tmp_path}/meta.db"
    command.upgrade(alembic_config(url), "head")
    settings = ApiSettings(environment=Environment.TEST, log_level="WARNING", database_url=url)

    def make() -> TestClient:
        return TestClient(
            create_app(settings, connector_factory=fake_connector, secrets=_secrets())
        )

    with make() as first:
        _create(first)
        assert first.get("/readyz").json()["checks"] == {"database": "ok"}
    with make() as second:  # new app instance, same database
        assert second.get(f"{PREFIX}/connections").json()["total"] == 1
