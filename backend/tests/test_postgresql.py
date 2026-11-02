import concurrent.futures
import os
import threading
import uuid
from datetime import datetime, timezone

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session as DBSession

from alembic import command
from app.auth.models import Session, SystemAdminRequest, User, UserRole
from app.auth.policy import Role
from app.auth.session import create_session
from app.config import Settings
from app.database import build_engine
from app.main import create_app

EXPECTED_REVISION = "0007_oidc_pkce_browser_binding"
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
    "admin_bootstrap_instance_state",
}


def _create_synthetic_test_db(prefix: str, namespace: str = "chpmis_013") -> str:
    base_url = os.environ["TEST_DATABASE_URL"]
    url_obj = make_url(base_url)
    db_name = f"{namespace}_{prefix}_{uuid.uuid4().hex[:8]}"
    admin_engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        admin_engine.dispose()
    new_url = url_obj.set(database=db_name)
    return new_url.render_as_string(hide_password=False)


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Dedicated PostgreSQL unavailable")
def test_postgresql_migration_head_and_readiness(monkeypatch):
    database_url = _create_synthetic_test_db("empty_to_head")
    monkeypatch.setenv("DATABASE_URL", database_url)
    settings = Settings(database_url=database_url)
    engine = build_engine(settings)
    assert engine is not None
    try:
        with engine.connect() as connection:
            assert len(inspect(connection).get_table_names()) == 0

        command.upgrade(Config("alembic.ini"), "head")

        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == EXPECTED_REVISION
            )
            tables = set(inspect(connection).get_table_names())
            assert tables == EXPECTED_TABLES
            assert len(tables) == 12

            inspector = inspect(connection)

            # 1. admin_bootstrap_instance_state columns and unique constraints
            inst_cols = {
                col["name"] for col in inspector.get_columns("admin_bootstrap_instance_state")
            }
            assert inst_cols == {"id", "instance_id", "created_at", "singleton_lock"}
            inst_uniques = {
                tuple(uc["column_names"])
                for uc in inspector.get_unique_constraints("admin_bootstrap_instance_state")
            }
            assert ("instance_id",) in inst_uniques
            assert ("singleton_lock",) in inst_uniques

            # 2. admin_bootstrap_receipts columns, unique, and foreign key constraints
            rcpt_cols = {col["name"] for col in inspector.get_columns("admin_bootstrap_receipts")}
            expected_rcpt_meta = {
                "instance_id",
                "request_id",
                "operator_id",
                "issued_at",
                "expires_at",
            }
            assert expected_rcpt_meta.issubset(rcpt_cols)
            expected_rcpt_base = {
                "id",
                "environment",
                "target_user1_id",
                "target_user2_id",
                "target_sub1",
                "target_sub2",
                "approver1_role",
                "approver1_key_fingerprint",
                "approver2_role",
                "approver2_key_fingerprint",
                "payload_digest",
                "created_at",
                "consumed",
                "single_bootstrap_lock",
            }
            assert expected_rcpt_base.issubset(rcpt_cols)
            rcpt_uniques = {
                tuple(uc["column_names"])
                for uc in inspector.get_unique_constraints("admin_bootstrap_receipts")
            }
            assert ("single_bootstrap_lock",) in rcpt_uniques
            rcpt_fks = {
                (
                    tuple(fk["constrained_columns"]),
                    fk["referred_table"],
                    tuple(fk["referred_columns"]),
                )
                for fk in inspector.get_foreign_keys("admin_bootstrap_receipts")
            }
            assert (("target_user1_id",), "users", ("id",)) in rcpt_fks
            assert (("target_user2_id",), "users", ("id",)) in rcpt_fks

            # 3. user_roles columns, nullability, and foreign keys
            ur_cols = {col["name"]: col for col in inspector.get_columns("user_roles")}
            assert ur_cols["granted_by"]["nullable"] is True
            assert "bootstrap_receipt_id" in ur_cols
            ur_fks = {
                (
                    tuple(fk["constrained_columns"]),
                    fk["referred_table"],
                    tuple(fk["referred_columns"]),
                )
                for fk in inspector.get_foreign_keys("user_roles")
            }
            assert (("bootstrap_receipt_id",), "admin_bootstrap_receipts", ("id",)) in ur_fks

            # 4. project_members unique constraint and foreign keys
            pm_uniques = {
                tuple(uc["column_names"])
                for uc in inspector.get_unique_constraints("project_members")
            }
            assert ("project_id", "user_id") in pm_uniques
            pm_fks = {
                (
                    tuple(fk["constrained_columns"]),
                    fk["referred_table"],
                    tuple(fk["referred_columns"]),
                )
                for fk in inspector.get_foreign_keys("project_members")
            }
            assert (("project_id",), "projects", ("id",)) in pm_fks
            assert (("user_id",), "users", ("id",)) in pm_fks

            # 5. tasks foreign keys
            task_fks = {
                (
                    tuple(fk["constrained_columns"]),
                    fk["referred_table"],
                    tuple(fk["referred_columns"]),
                )
                for fk in inspector.get_foreign_keys("tasks")
            }
            assert (("project_id",), "projects", ("id",)) in task_fks

            # 6. oidc_states columns
            oidc_cols = {col["name"] for col in inspector.get_columns("oidc_states")}
            assert {
                "state",
                "nonce",
                "redirect_uri",
                "created_at",
                "expires_at",
                "code_verifier",
                "binding_digest",
            }.issubset(oidc_cols)

        with TestClient(create_app(settings)) as client:
            assert client.get("/health/ready").status_code == 200
    finally:
        engine.dispose()


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Dedicated PostgreSQL unavailable")
def test_postgresql_upgrade_from_0005_with_synthetic_rows_preserves_data(monkeypatch):
    database_url = _create_synthetic_test_db("pop_0005_head")
    monkeypatch.setenv("DATABASE_URL", database_url)
    settings = Settings(database_url=database_url)
    engine = build_engine(settings)
    assert engine is not None
    try:
        # 1. Upgrade to 0005_initial_admin_bootstrap
        command.upgrade(Config("alembic.ini"), "0005_initial_admin_bootstrap")
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0005_initial_admin_bootstrap"
            )
            tables_0005 = set(inspect(connection).get_table_names())
            assert len(tables_0005) == 11
            assert "admin_bootstrap_instance_state" not in tables_0005

        # 2. Insert synthetic rows into users, admin_bootstrap_receipts, and user_roles
        prefix = f"syn5_{uuid.uuid4().hex[:8]}"
        u1_id = f"{prefix}_u1"
        u2_id = f"{prefix}_u2"
        receipt_id = f"{prefix}_rcpt"
        role_id = f"{prefix}_role"
        now_dt = datetime.now(timezone.utc)

        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users (id, sub, email, name, is_active, created_at, updated_at) "
                    "VALUES (:u1_id, :u1_sub, :u1_email, :u1_name, true, :now, :now), "
                    "(:u2_id, :u2_sub, :u2_email, :u2_name, true, :now, :now)"
                ),
                {
                    "u1_id": u1_id,
                    "u1_sub": f"{prefix}_sub1",
                    "u1_email": f"{prefix}_u1@example.com",
                    "u1_name": "Synthetic User 1",
                    "u2_id": u2_id,
                    "u2_sub": f"{prefix}_sub2",
                    "u2_email": f"{prefix}_u2@example.com",
                    "u2_name": "Synthetic User 2",
                    "now": now_dt,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO admin_bootstrap_receipts ("
                    "  id, environment, target_user1_id, target_user2_id, "
                    "  target_sub1, target_sub2, approver1_role, approver1_key_fingerprint, "
                    "  approver2_role, approver2_key_fingerprint, payload_digest, "
                    "  created_at, consumed, single_bootstrap_lock"
                    ") VALUES ("
                    "  :id, :environment, :target_user1_id, :target_user2_id, "
                    "  :target_sub1, :target_sub2, :approver1_role, :approver1_key_fingerprint, "
                    "  :approver2_role, :approver2_key_fingerprint, :payload_digest, "
                    "  :created_at, :consumed, :single_bootstrap_lock"
                    ")"
                ),
                {
                    "id": receipt_id,
                    "environment": "synthetic_staging",
                    "target_user1_id": u1_id,
                    "target_user2_id": u2_id,
                    "target_sub1": f"{prefix}_sub1",
                    "target_sub2": f"{prefix}_sub2",
                    "approver1_role": "sec_lead",
                    "approver1_key_fingerprint": "1" * 64,
                    "approver2_role": "infra_lead",
                    "approver2_key_fingerprint": "2" * 64,
                    "payload_digest": "3" * 64,
                    "created_at": now_dt,
                    "consumed": True,
                    "single_bootstrap_lock": "BOOTSTRAP_LOCK",
                },
            )
            connection.execute(
                text(
                    "INSERT INTO user_roles ("
                    "  id, user_id, role, granted_by, created_at, bootstrap_receipt_id"
                    ") VALUES ("
                    "  :id, :user_id, :role, NULL, :now, :bootstrap_receipt_id"
                    ")"
                ),
                {
                    "id": role_id,
                    "user_id": u1_id,
                    "role": "system_admin",
                    "now": now_dt,
                    "bootstrap_receipt_id": receipt_id,
                },
            )

        # 3. Upgrade from 0005 to head (0006)
        command.upgrade(Config("alembic.ini"), "head")

        # 4. Verify migration head reached and rows preserved
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == EXPECTED_REVISION
            )
            tables_0006 = set(inspect(connection).get_table_names())
            assert tables_0006 == EXPECTED_TABLES
            assert len(tables_0006) == 12

            # Verify receipt row preservation and new column values
            rcpt_row = (
                connection.execute(
                    text("SELECT * FROM admin_bootstrap_receipts WHERE id = :id"),
                    {"id": receipt_id},
                )
                .mappings()
                .one()
            )
            assert rcpt_row["id"] == receipt_id
            assert rcpt_row["environment"] == "synthetic_staging"
            assert rcpt_row["target_user1_id"] == u1_id
            assert rcpt_row["target_user2_id"] == u2_id
            assert rcpt_row["consumed"] is True
            assert rcpt_row["instance_id"] is None
            assert rcpt_row["request_id"] is None
            assert rcpt_row["operator_id"] is None
            assert rcpt_row["issued_at"] is None
            assert rcpt_row["expires_at"] is None

            # Verify user_roles row preservation
            role_row = (
                connection.execute(
                    text("SELECT * FROM user_roles WHERE id = :id"),
                    {"id": role_id},
                )
                .mappings()
                .one()
            )
            assert role_row["user_id"] == u1_id
            assert role_row["role"] == "system_admin"
            assert role_row["granted_by"] is None
            assert role_row["bootstrap_receipt_id"] == receipt_id

            # Verify users preserved
            users_count = connection.execute(
                text("SELECT count(*) FROM users WHERE id IN (:u1, :u2)"),
                {"u1": u1_id, "u2": u2_id},
            ).scalar_one()
            assert users_count == 2
    finally:
        engine.dispose()


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Dedicated PostgreSQL unavailable")
def test_postgresql_upgrade_from_0006_preserves_oidc_state_rows_and_nullable_pkce_fields(
    monkeypatch,
):
    database_url = _create_synthetic_test_db("pop_0006_head")
    monkeypatch.setenv("DATABASE_URL", database_url)
    settings = Settings(database_url=database_url)
    engine = build_engine(settings)
    assert engine is not None
    try:
        # 1. Upgrade to 0006_bootstrap_trust_boundary
        command.upgrade(Config("alembic.ini"), "0006_bootstrap_trust_boundary")
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0006_bootstrap_trust_boundary"
            )
            inspector_0006 = inspect(connection)
            cols_0006 = {col["name"] for col in inspector_0006.get_columns("oidc_states")}
            assert "code_verifier" not in cols_0006
            assert "binding_digest" not in cols_0006

        # 2. Insert synthetic row into oidc_states with 0006 columns
        test_state = f"syn006_state_{uuid.uuid4().hex[:8]}"
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO oidc_states (state, nonce, redirect_uri, created_at, expires_at) "
                    "VALUES (:state, :nonce, :redirect_uri, :created_at, :expires_at)"
                ),
                {
                    "state": test_state,
                    "nonce": "syn006_nonce",
                    "redirect_uri": "http://127.0.0.1:8000/api/v1/auth/callback",
                    "created_at": 1700000000.0,
                    "expires_at": 1700000600.0,
                },
            )

        # 3. Upgrade to head
        command.upgrade(Config("alembic.ini"), "head")
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == EXPECTED_REVISION
            )
            # Verify synthetic oidc_state row is preserved with nullable new columns
            state_row = (
                connection.execute(
                    text("SELECT * FROM oidc_states WHERE state = :state"),
                    {"state": test_state},
                )
                .mappings()
                .one()
            )
            assert state_row["state"] == test_state
            assert state_row["nonce"] == "syn006_nonce"
            assert state_row["redirect_uri"] == "http://127.0.0.1:8000/api/v1/auth/callback"
            assert state_row["code_verifier"] is None
            assert state_row["binding_digest"] is None
    finally:
        engine.dispose()


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Dedicated PostgreSQL unavailable")
def test_postgresql_receipt_immutability_trigger_blocks_mutations(monkeypatch):
    database_url = _create_synthetic_test_db("receipt_trigger")
    monkeypatch.setenv("DATABASE_URL", database_url)
    settings = Settings(database_url=database_url)
    engine = build_engine(settings)
    assert engine is not None
    try:
        command.upgrade(Config("alembic.ini"), "head")
        prefix = f"trg_{uuid.uuid4().hex[:8]}"
        u1_id = f"{prefix}_u1"
        u2_id = f"{prefix}_u2"
        receipt_id = f"{prefix}_rcpt"
        now_dt = datetime.now(timezone.utc)

        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users (id, sub, email, name, is_active, created_at, updated_at) "
                    "VALUES (:u1_id, :u1_sub, :u1_email, :u1_name, true, :now, :now), "
                    "(:u2_id, :u2_sub, :u2_email, :u2_name, true, :now, :now)"
                ),
                {
                    "u1_id": u1_id,
                    "u1_sub": f"{prefix}_sub1",
                    "u1_email": f"{prefix}_u1@example.com",
                    "u1_name": "Trigger Test User 1",
                    "u2_id": u2_id,
                    "u2_sub": f"{prefix}_sub2",
                    "u2_email": f"{prefix}_u2@example.com",
                    "u2_name": "Trigger Test User 2",
                    "now": now_dt,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO admin_bootstrap_receipts ("
                    "  id, environment, target_user1_id, target_user2_id, "
                    "  target_sub1, target_sub2, approver1_role, approver1_key_fingerprint, "
                    "  approver2_role, approver2_key_fingerprint, payload_digest, "
                    "  created_at, consumed, single_bootstrap_lock, "
                    "  instance_id, request_id, operator_id, issued_at, expires_at"
                    ") VALUES ("
                    "  :id, :environment, :target_user1_id, :target_user2_id, "
                    "  :target_sub1, :target_sub2, :approver1_role, :approver1_key_fingerprint, "
                    "  :approver2_role, :approver2_key_fingerprint, :payload_digest, "
                    "  :created_at, :consumed, :single_bootstrap_lock, "
                    "  :instance_id, :request_id, :operator_id, :issued_at, :expires_at"
                    ")"
                ),
                {
                    "id": receipt_id,
                    "environment": "synthetic_env",
                    "target_user1_id": u1_id,
                    "target_user2_id": u2_id,
                    "target_sub1": f"{prefix}_sub1",
                    "target_sub2": f"{prefix}_sub2",
                    "approver1_role": "sec_lead",
                    "approver1_key_fingerprint": "1" * 64,
                    "approver2_role": "infra_lead",
                    "approver2_key_fingerprint": "2" * 64,
                    "payload_digest": "3" * 64,
                    "created_at": now_dt,
                    "consumed": True,
                    "single_bootstrap_lock": "BOOTSTRAP_LOCK",
                    "instance_id": f"{prefix}_inst",
                    "request_id": f"{prefix}_req",
                    "operator_id": "operator_admin",
                    "issued_at": now_dt,
                    "expires_at": now_dt,
                },
            )

        with engine.connect() as connection:
            # 1. Attempt UPDATE -> blocked by PostgreSQL trigger
            with pytest.raises(DBAPIError) as exc_update:
                with connection.begin_nested():
                    connection.execute(
                        text(
                            "UPDATE admin_bootstrap_receipts "
                            "SET environment = 'tampered' WHERE id = :id"
                        ),
                        {"id": receipt_id},
                    )
            assert "admin_bootstrap_receipts rows are immutable" in str(exc_update.value)

            # 2. Attempt DELETE -> blocked by PostgreSQL trigger
            with pytest.raises(DBAPIError) as exc_delete:
                with connection.begin_nested():
                    connection.execute(
                        text("DELETE FROM admin_bootstrap_receipts WHERE id = :id"),
                        {"id": receipt_id},
                    )
            assert "admin_bootstrap_receipts rows are immutable" in str(exc_delete.value)

            # 3. Verify receipt remains intact
            remaining = (
                connection.execute(
                    text("SELECT id, environment FROM admin_bootstrap_receipts WHERE id = :id"),
                    {"id": receipt_id},
                )
                .mappings()
                .one()
            )
            assert remaining["id"] == receipt_id
            assert remaining["environment"] == "synthetic_env"
    finally:
        engine.dispose()


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Dedicated PostgreSQL unavailable")
def test_postgresql_concurrent_approval_serialized(monkeypatch):
    """Test two concurrent attempts to approve the same request on PostgreSQL.

    Exactly one approval succeeds, the other receives conflict, and effects occur once.
    """
    database_url = _create_synthetic_test_db("concurrent_appr")
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


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Dedicated PostgreSQL unavailable")
def test_postgresql_distinct_requests_same_target_concurrency(monkeypatch):
    """Test two distinct pending grant requests for the same target user racing on PostgreSQL.

    Synchronizes both approvals before the target-user lookup and verifies target-row serialization.
    Safe expected contract: exactly one approval succeeds (200), one receives conflict (409),
    and exactly one active canonical system_admin role exists for the target.
    """
    database_url = _create_synthetic_test_db("distinct_target", namespace="chpmis_015_f6")
    monkeypatch.setenv("DATABASE_URL", database_url)
    command.upgrade(Config("alembic.ini"), "head")
    settings = Settings(database_url=database_url)
    engine = build_engine(settings)
    assert engine is not None

    prefix = f"syn_dist_{uuid.uuid4().hex[:8]}"
    app = create_app(settings)

    barrier = threading.Barrier(2, timeout=10.0)
    target_user_id = None

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if "FROM users" in statement and target_user_id is not None:
            is_target_role_query = False
            if isinstance(parameters, dict):
                if any(v == target_user_id for v in parameters.values()):
                    is_target_role_query = True
            elif isinstance(parameters, (list, tuple)):
                if target_user_id in parameters:
                    is_target_role_query = True
            elif str(target_user_id) in str(parameters):
                is_target_role_query = True

            if is_target_role_query:
                try:
                    barrier.wait()
                except threading.BrokenBarrierError:
                    pass

    try:
        with DBSession(bind=engine) as db:
            seed_admin = User(
                id=f"{prefix}_seed",
                sub=f"{prefix}_sub_seed",
                email=f"{prefix}_seed@example.com",
                name="PostgreSQL Seed Admin",
                is_active=True,
            )
            req1 = User(
                id=f"{prefix}_req1",
                sub=f"{prefix}_sub_req1",
                email=f"{prefix}_req1@example.com",
                name="PostgreSQL Requester Admin 1",
                is_active=True,
            )
            req2 = User(
                id=f"{prefix}_req2",
                sub=f"{prefix}_sub_req2",
                email=f"{prefix}_req2@example.com",
                name="PostgreSQL Requester Admin 2",
                is_active=True,
            )
            app1 = User(
                id=f"{prefix}_app1",
                sub=f"{prefix}_sub_app1",
                email=f"{prefix}_app1@example.com",
                name="PostgreSQL Approver Admin 1",
                is_active=True,
            )
            app2 = User(
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
            db.add_all([seed_admin, req1, req2, app1, app2, target_user])
            db.commit()

            db.add_all(
                [
                    UserRole(
                        user_id=req1.id,
                        role=Role.SYSTEM_ADMIN.value,
                        granted_by=seed_admin.id,
                    ),
                    UserRole(
                        user_id=req2.id,
                        role=Role.SYSTEM_ADMIN.value,
                        granted_by=seed_admin.id,
                    ),
                    UserRole(
                        user_id=app1.id,
                        role=Role.SYSTEM_ADMIN.value,
                        granted_by=seed_admin.id,
                    ),
                    UserRole(
                        user_id=app2.id,
                        role=Role.SYSTEM_ADMIN.value,
                        granted_by=seed_admin.id,
                    ),
                ]
            )
            db.commit()

            sess_app1 = create_session(db, app1.id, settings)
            sess_app2 = create_session(db, app2.id, settings)
            sess_tgt = create_session(db, target_user.id, settings)

            req_a = SystemAdminRequest(
                id=f"{prefix}_req_a",
                target_user_id=target_user.id,
                action="grant",
                status="pending",
                requester_id=req1.id,
            )
            req_b = SystemAdminRequest(
                id=f"{prefix}_req_b",
                target_user_id=target_user.id,
                action="grant",
                status="pending",
                requester_id=req2.id,
            )
            db.add_all([req_a, req_b])
            db.commit()

            req_a_id = req_a.id
            req_b_id = req_b.id
            sess1_id = sess_app1.id
            csrf1 = sess_app1.csrf_token
            sess2_id = sess_app2.id
            csrf2 = sess_app2.csrf_token
            tgt_sess_id = sess_tgt.id
            target_user_id = target_user.id

        event.listen(engine, "before_cursor_execute", before_cursor_execute)

        results = []

        def call_approve(sess_id, csrf, request_id):
            with TestClient(app) as client:
                client.cookies.set("pmis_session", sess_id)
                res = client.post(
                    "/api/v1/auth/roles/system-admin/approve",
                    json={"request_id": request_id},
                    headers={"X-CSRF-Token": csrf},
                )
                results.append((res.status_code, res.json()))

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(call_approve, sess1_id, csrf1, req_a_id)
            f2 = executor.submit(call_approve, sess2_id, csrf2, req_b_id)
            f1.result()
            f2.result()

        status_codes = [r[0] for r in results]
        assert sorted(status_codes) == [200, 409], f"Expected one 200 and one 409: {results}"
        conflict_result = next(r for r in results if r[0] == 409)
        assert (
            "already" in conflict_result[1].get("detail", "").lower()
            or "conflict" in conflict_result[1].get("detail", "").lower()
        )

        with DBSession(bind=engine) as verify_db:
            roles = (
                verify_db.query(UserRole)
                .filter_by(user_id=target_user_id, role=Role.SYSTEM_ADMIN.value)
                .all()
            )
            assert len(roles) == 1, (
                f"Expected exactly 1 active canonical system_admin role, found {len(roles)}"
            )

            tgt_sess = verify_db.query(Session).filter_by(id=tgt_sess_id).first()
            assert tgt_sess is not None
            assert tgt_sess.is_revoked is True

            req_a_db = verify_db.query(SystemAdminRequest).filter_by(id=req_a_id).first()
            req_b_db = verify_db.query(SystemAdminRequest).filter_by(id=req_b_id).first()
            assert req_a_db is not None and req_b_db is not None
            approved_count = sum(1 for r in (req_a_db, req_b_db) if r.status == "approved")
            assert approved_count == 1, (
                f"Expected exactly 1 approved request, found {approved_count}"
            )
            pending_count = sum(1 for r in (req_a_db, req_b_db) if r.status == "pending")
            assert pending_count == 1, f"Expected exactly 1 pending request, found {pending_count}"
    finally:
        try:
            event.remove(engine, "before_cursor_execute", before_cursor_execute)
        except Exception:
            pass
        engine.dispose()
