import concurrent.futures
import os
import uuid

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session as DBSession

from alembic import command
from app.auth.models import Session, SystemAdminRequest, User, UserRole
from app.auth.policy import Role
from app.auth.session import create_session
from app.config import Settings
from app.database import build_engine
from app.main import create_app

EXPECTED_REVISION = "0005_initial_admin_bootstrap"
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
    "admin_bootstrap_receipts",
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


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Dedicated PostgreSQL unavailable")
def test_postgresql_concurrent_approval_serialized(monkeypatch):
    """Test two concurrent attempts to approve the same request on PostgreSQL.

    Exactly one approval succeeds, the other receives conflict, and effects occur once.
    """
    database_url = os.environ["TEST_DATABASE_URL"]
    monkeypatch.setenv("DATABASE_URL", database_url)
    command.upgrade(Config("alembic.ini"), "head")
    settings = Settings(database_url=database_url)
    engine = build_engine(settings)
    assert engine is not None

    prefix = f"syn_{uuid.uuid4().hex[:8]}"
    app = create_app(settings)

    try:
        with DBSession(bind=engine) as db:
            admin_seed = User(
                id=f"{prefix}_seed",
                sub=f"{prefix}_sub_seed",
                email=f"{prefix}_seed@example.com",
                name="PostgreSQL Seed Admin",
                is_active=True,
            )
            admin_req = User(
                id=f"{prefix}_req",
                sub=f"{prefix}_sub_req",
                email=f"{prefix}_req@example.com",
                name="PostgreSQL Requester Admin",
                is_active=True,
            )
            admin_app1 = User(
                id=f"{prefix}_app1",
                sub=f"{prefix}_sub_app1",
                email=f"{prefix}_app1@example.com",
                name="PostgreSQL Approver Admin 1",
                is_active=True,
            )
            admin_app2 = User(
                id=f"{prefix}_app2",
                sub=f"{prefix}_sub_app2",
                email=f"{prefix}_app2@example.com",
                name="PostgreSQL Approver Admin 2",
                is_active=True,
            )
            target_user = User(
                id=f"{prefix}_tgt",
                sub=f"{prefix}_sub_tgt",
                email=f"{prefix}_tgt@example.com",
                name="PostgreSQL Target User",
                is_active=True,
            )
            db.add_all([admin_seed, admin_req, admin_app1, admin_app2, target_user])
            db.commit()

            db.add(
                UserRole(
                    user_id=admin_req.id,
                    role=Role.SYSTEM_ADMIN.value,
                    granted_by=admin_seed.id,
                )
            )
            db.add(
                UserRole(
                    user_id=admin_app1.id,
                    role=Role.SYSTEM_ADMIN.value,
                    granted_by=admin_seed.id,
                )
            )
            db.add(
                UserRole(
                    user_id=admin_app2.id,
                    role=Role.SYSTEM_ADMIN.value,
                    granted_by=admin_seed.id,
                )
            )
            db.commit()

            sess_app1 = create_session(db, admin_app1.id, settings)
            sess_app2 = create_session(db, admin_app2.id, settings)
            sess_tgt = create_session(db, target_user.id, settings)

            req = SystemAdminRequest(
                id=f"{prefix}_req_id",
                target_user_id=target_user.id,
                action="grant",
                status="pending",
                requester_id=admin_req.id,
            )
            db.add(req)
            db.commit()

            req_id = req.id
            sess1_id = sess_app1.id
            csrf1 = sess_app1.csrf_token
            sess2_id = sess_app2.id
            csrf2 = sess_app2.csrf_token
            tgt_sess_id = sess_tgt.id
            target_user_id = target_user.id
            admin_app1_id = admin_app1.id
            admin_app2_id = admin_app2.id

        results = []

        def call_approve(sess_id, csrf):
            with TestClient(app) as client:
                client.cookies.set("pmis_session", sess_id)
                res = client.post(
                    "/api/v1/auth/roles/system-admin/approve",
                    json={"request_id": req_id},
                    headers={"X-CSRF-Token": csrf},
                )
                results.append((res.status_code, res.json()))

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(call_approve, sess1_id, csrf1)
            f2 = executor.submit(call_approve, sess2_id, csrf2)
            f1.result()
            f2.result()

        status_codes = [r[0] for r in results]
        assert sorted(status_codes) == [200, 409], f"Expected one 200 and one 409: {results}"
        conflict_result = next(r for r in results if r[0] == 409)
        assert "already decided" in conflict_result[1].get("detail", "")

        with DBSession(bind=engine) as verify_db:
            # Role granted exactly once
            roles = (
                verify_db.query(UserRole)
                .filter_by(user_id=target_user_id, role=Role.SYSTEM_ADMIN.value)
                .all()
            )
            assert len(roles) == 1

            # Target session revoked
            tgt_sess = verify_db.query(Session).filter_by(id=tgt_sess_id).first()
            assert tgt_sess is not None
            assert tgt_sess.is_revoked is True

            # Request row approved
            req_db = verify_db.query(SystemAdminRequest).filter_by(id=req_id).first()
            assert req_db is not None
            assert req_db.status == "approved"
            assert req_db.approver_id in (admin_app1_id, admin_app2_id)
            assert req_db.decided_at is not None
    finally:
        engine.dispose()
