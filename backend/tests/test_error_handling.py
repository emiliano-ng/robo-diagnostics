from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import app
from app.database import get_db


def test_operational_error_returns_503_with_consistent_shape():
    """If the DB connection drops mid-request, the client should get a
    503 with a clear machine-readable error code — not a raw traceback
    or a generic 500 indistinguishable from an actual bug in our code.
    """

    def broken_db():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))
        yield  # pragma: no cover — unreachable, keeps this a generator

    app.dependency_overrides[get_db] = broken_db
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/experiments")

    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["error"] == "database_unavailable"


def test_unhandled_exception_returns_500_without_leaking_internals():
    """Any other unexpected exception should still produce a clean JSON
    500 — the client never sees a stack trace or internal exception text.
    """

    def broken_db():
        raise RuntimeError("something unrelated to the database broke")
        yield  # pragma: no cover

    app.dependency_overrides[get_db] = broken_db
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/experiments")

    app.dependency_overrides.clear()

    assert response.status_code == 500
    body = response.json()
    assert body["error"] == "internal_error"
    assert "RuntimeError" not in body["detail"]
    assert "something unrelated" not in body["detail"]
