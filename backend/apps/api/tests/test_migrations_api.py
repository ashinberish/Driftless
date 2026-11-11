from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from driftless_api.main import create_app
from driftless_api.settings import ApiSettings
from driftless_core.config import Environment
from driftless_core.secrets import EnvSecretResolver, SecretResolverRegistry

PREFIX = "/api/v1"


@pytest.fixture
def client(fake_connector: Any) -> Iterator[TestClient]:
    app = create_app(
        ApiSettings(environment=Environment.TEST, log_level="WARNING"),
        connector_factory=fake_connector,
        secrets=SecretResolverRegistry([EnvSecretResolver({"PW": "x"})]),
    )
    with TestClient(app) as c:
        yield c


def _connection(client: TestClient, name: str = "shop") -> str:
    res = client.post(
        f"{PREFIX}/connections",
        json={
            "name": name,
            "engine": "postgres",
            "host": "db",
            "port": 5432,
            "database": "shop",
            "username": "ro",
            "secret_ref": "env:PW",
        },
    )
    assert res.status_code == 201, res.text
    return str(res.json()["id"])


def _migration(client: TestClient, source: str, **overrides: object) -> dict[str, Any]:
    body: dict[str, object] = {
        "name": "shop-to-pg17",
        "source_connection_id": source,
        "target_engine": "postgres",
    }
    body.update(overrides)
    res = client.post(f"{PREFIX}/migrations", json=body)
    assert res.status_code == 201, res.text
    return res.json()


def test_create_draft_and_list(client: TestClient) -> None:
    source = _connection(client)
    m = _migration(client, source)
    assert m["status"] == "draft"
    assert m["source_engine"] == "postgres"
    assert client.get(f"{PREFIX}/migrations").json()["total"] == 1


def test_assessment_runs_against_live_catalog_and_updates_status(client: TestClient) -> None:
    m = _migration(client, _connection(client))
    assert client.get(f"{PREFIX}/migrations/{m['id']}/assessments/latest").status_code == 404

    res = client.post(f"{PREFIX}/migrations/{m['id']}/assessments")
    assert res.status_code == 201
    run = res.json()
    a = run["assessment"]
    # The fake catalog has one table without a primary key -> blocking.
    assert a["ready"] is False
    assert a["tables"] == 2
    assert {f["rule_id"] for f in a["findings"]} >= {"no-primary-key"}
    assert 0 <= a["readiness_pct"] <= 100
    assert a["effort_days_min"] <= a["effort_days_max"]

    assert client.get(f"{PREFIX}/migrations/{m['id']}").json()["status"] == "needs_attention"
    latest = client.get(f"{PREFIX}/migrations/{m['id']}/assessments/latest").json()
    assert latest["id"] == run["id"]


def test_markdown_report_download(client: TestClient) -> None:
    m = _migration(client, _connection(client))
    client.post(f"{PREFIX}/migrations/{m['id']}/assessments")
    res = client.get(f"{PREFIX}/migrations/{m['id']}/assessments/latest/report.md")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/markdown")
    assert "attachment" in res.headers["content-disposition"]
    assert res.text.startswith("# Migration assessment: shop-to-pg17")


@pytest.mark.parametrize(
    ("overrides", "status"),
    [
        ({"target_engine": "db2"}, 404),
        ({"source_connection_id": "conn_missing"}, 404),
        ({"name": ""}, 422),
    ],
)
def test_invalid_drafts_rejected(
    client: TestClient, overrides: dict[str, object], status: int
) -> None:
    source = _connection(client)
    body: dict[str, object] = {
        "name": "m",
        "source_connection_id": source,
        "target_engine": "postgres",
    }
    body.update(overrides)
    assert client.post(f"{PREFIX}/migrations", json=body).status_code == status


def test_target_connection_must_match_engine_and_differ(client: TestClient) -> None:
    source = _connection(client, "a")
    res = client.post(
        f"{PREFIX}/migrations",
        json={
            "name": "m",
            "source_connection_id": source,
            "target_engine": "postgres",
            "target_connection_id": source,
        },
    )
    assert res.status_code == 409
    res = client.post(
        f"{PREFIX}/migrations",
        json={
            "name": "m",
            "source_connection_id": source,
            "target_engine": "mysql",
            "target_connection_id": _connection(client, "b"),
        },
    )
    assert res.status_code == 400


def test_connection_used_by_migration_cannot_be_deleted(client: TestClient) -> None:
    source = _connection(client)
    _migration(client, source)
    res = client.delete(f"{PREFIX}/connections/{source}")
    assert res.status_code == 409
    assert "used by a migration" in res.json()["error"]["message"]
