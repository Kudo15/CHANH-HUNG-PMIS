from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.database import get_engine
from app.main import create_app

app = create_app(Settings(database_url=None))


def test_live_returns_ok():
    with TestClient(app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reflects_database_availability():
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unavailable"}


def test_ready_checks_database_on_each_request_and_keeps_failure_private(monkeypatch):
    # SQLite exercises our SELECT boundary locally; PostgreSQL is checked separately in CI.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    app.dependency_overrides[get_engine] = lambda: engine
    try:
        with TestClient(app) as client:
            healthy = client.get("/health/ready")
            assert healthy.status_code == 200
            assert healthy.json() == {"status": "ready", "database": "available"}

            def fail_connect():
                raise OperationalError("SELECT 1", {}, Exception("private-connection-details"))

            monkeypatch.setattr(engine, "connect", fail_connect)
            unavailable = client.get("/health/ready")
            assert unavailable.status_code == 503
            assert unavailable.json() == {"status": "not_ready", "database": "unavailable"}
            assert client.get("/health/live").status_code == 200
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
