import os

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from alembic import command
from app.config import Settings
from app.database import build_engine
from app.main import create_app

EXPECTED_REVISION = "0004_projects_tasks_audit"
EXPECTED_TABLES = {
    "alembic_version",
    "users",
    "user_roles",
    "sessions",
    "oidc_states",
    "system_admin_requests",
    "projects",
    "project_members",
    "tasks",
    "audit_events",
}


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Dedicated PostgreSQL unavailable")
def test_postgresql_migration_head_and_readiness(monkeypatch):
    # Use a dedicated disposable database. This test never resets or drops data.
    database_url = os.environ["TEST_DATABASE_URL"]
    monkeypatch.setenv("DATABASE_URL", database_url)
    command.upgrade(Config("alembic.ini"), "head")
    settings = Settings(database_url=database_url)
    engine = build_engine(settings)
    assert engine is not None
    try:
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == EXPECTED_REVISION
            )
            assert set(inspect(connection).get_table_names()) == EXPECTED_TABLES
        with TestClient(create_app(settings)) as client:
            assert client.get("/health/ready").status_code == 200
    finally:
        engine.dispose()
