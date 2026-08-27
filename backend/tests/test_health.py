from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_ok_when_db_is_reachable():
    # This test runs with a real Postgres available (same as the rest of
    # the suite), so the health check's actual DB query succeeds.
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "up"


def test_health_returns_503_when_db_is_unreachable(monkeypatch):
    # Simulate DB being down without actually stopping Postgres —
    # patch the check function the endpoint calls.
    monkeypatch.setattr("app.main.check_db_connection", lambda: False)

    response = client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"] == "down"
