from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from driftless_api.main import create_app
from driftless_api.settings import ApiSettings
from driftless_core.config import Environment

PREFIX = "/api/v1"


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(ApiSettings(environment=Environment.TEST, log_level="WARNING"))
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
        "secret_ref": "vault:db/billing-ro",
    }
    body.update(overrides)
    return body


def test_health_and_request_id(client: TestClient) -> None:
    res = client.get("/healthz", headers={"X-Request-ID": "req-test"})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.headers["X-Request-ID"] == "req-test"


def test_list_connectors(client: TestClient) -> None:
    engines = {c["engine"] for c in client.get(f"{PREFIX}/connectors").json()}
    assert {"postgres", "mysql"} <= engines


def test_connection_crud(client: TestClient) -> None:
    created = client.post(f"{PREFIX}/connections", json=_payload())
    assert created.status_code == 201
    conn = created.json()
    assert conn["id"].startswith("conn_")
    assert "password" not in conn

    listed = client.get(f"{PREFIX}/connections").json()
    assert listed["total"] == 1

    assert client.get(f"{PREFIX}/connections/{conn['id']}").json()["name"] == "billing-prod"
    assert client.delete(f"{PREFIX}/connections/{conn['id']}").status_code == 204
    missing = client.get(f"{PREFIX}/connections/{conn['id']}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_duplicate_name_conflicts(client: TestClient) -> None:
    client.post(f"{PREFIX}/connections", json=_payload())
    res = client.post(f"{PREFIX}/connections", json=_payload())
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "conflict"


def test_unknown_engine_rejected(client: TestClient) -> None:
    res = client.post(f"{PREFIX}/connections", json=_payload(engine="db2"))
    assert res.status_code == 404
    assert "postgres" in res.json()["error"]["details"]["available"]


def test_plaintext_secret_ref_rejected(client: TestClient) -> None:
    res = client.post(f"{PREFIX}/connections", json=_payload(secret_ref="hunter2"))
    assert res.status_code == 422
