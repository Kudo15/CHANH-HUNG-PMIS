from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.models import User, UserRole
from app.auth.policy import Role
from app.auth.session import create_session
from app.config import Settings
from app.database import Base
from app.main import create_app
from app.projects.models import AuditEvent, Project, Task


def setup_test_env():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
    )

    settings = Settings(
        database_url=None,
        session_idle_timeout_minutes=30,
        session_absolute_timeout_hours=12,
    )
    app = create_app(settings)
    app.state.engine = engine
    return app, TestingSessionLocal, settings, engine


def create_user_and_session(db, settings, user_id: str, email: str, role: Role | None = None):
    user = User(
        id=user_id,
        sub=f"sub_{user_id}",
        email=email,
        name=f"User {user_id}",
        is_active=True,
    )
    db.add(user)
    if role:
        user_role = UserRole(
            id=f"ur_{user_id}_{role.value}",
            user_id=user.id,
            role=role.value,
            granted_by="system",
        )
        db.add(user_role)
    db.commit()

    session = create_session(db, user.id, settings)
    return user, session


def test_audit_event_allowlist_excludes_free_form_text_and_secrets_ac12():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-audit-1", "pmaudit1@example.com", Role.PROJECT_MANAGER
            )

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)

        # 1. Project create audit
        p_resp = client.post(
            "/api/v1/projects",
            json={
                "name": "Synthetic Project 202",
                "description": "Sensitive confidential freeform text that must NOT be audited",
                "lead_department_id": "dept-opaque-synthetic-01",
            },
            headers={"X-CSRF-Token": pm_sess.csrf_token, "X-Correlation-ID": "corr-audit-01"},
        )
        assert p_resp.status_code == 201
        p_id = p_resp.json()["id"]

        with SessionLocal() as db:
            p_audit = (
                db.query(AuditEvent).filter_by(target_id=p_id, action="project:create").first()
            )
            assert p_audit is not None
            # Allowlist check: description, name, secrets and freeform text MUST be absent
            assert "description" not in p_audit.after_values
            assert "name" not in p_audit.after_values
            assert "secret" not in p_audit.after_values
            assert p_audit.after_values.keys() <= {
                "lead_department_id",
                "project_manager_id",
                "start_date",
                "end_date",
                "lifecycle",
            }

        # 2. Task create audit
        t_resp = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={
                "title": "Synthetic Task 202",
                "description": "Another secret note with tokens and freeform documentation",
            },
            headers={"X-CSRF-Token": pm_sess.csrf_token, "X-Correlation-ID": "corr-audit-02"},
        )
        assert t_resp.status_code == 201
        t_id = t_resp.json()["id"]

        with SessionLocal() as db:
            t_audit = db.query(AuditEvent).filter_by(target_id=t_id, action="task:create").first()
            assert t_audit is not None
            assert "description" not in t_audit.after_values
            assert "title" not in t_audit.after_values
            assert t_audit.after_values.keys() <= {
                "project_id",
                "creator_id",
                "assignee_id",
                "due_date",
                "status",
            }
    finally:
        engine.dispose()


def test_transaction_rollback_when_audit_insert_fails_ac12():
    """Verify that project and task mutations roll back completely if audit insertion fails."""
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-rollback", "pmrollback@example.com", Role.PROJECT_MANAGER
            )

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)

        # 1. Simulate failure during audit insertion for project creation
        with patch(
            "app.projects.service.record_audit_event",
            side_effect=RuntimeError("Simulated DB audit crash"),
        ):
            resp = client.post(
                "/api/v1/projects",
                json={"name": "Synthetic Rollback Project"},
                headers={"X-CSRF-Token": pm_sess.csrf_token},
            )
            assert resp.status_code == 500

        # Verify that project was NOT persisted (rolled back)
        with SessionLocal() as db:
            proj = db.query(Project).filter_by(name="Synthetic Rollback Project").first()
            assert proj is None, "Project mutation should have been rolled back on audit failure"

        # 2. Normal project creation succeeds
        p_resp = client.post(
            "/api/v1/projects",
            json={"name": "Synthetic Safe Project"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert p_resp.status_code == 201
        p_id = p_resp.json()["id"]

        # 3. Simulate failure during audit insertion for task creation
        with patch(
            "app.projects.service.record_audit_event",
            side_effect=RuntimeError("Simulated task audit crash"),
        ):
            t_resp = client.post(
                f"/api/v1/projects/{p_id}/tasks",
                json={"title": "Synthetic Rollback Task"},
                headers={"X-CSRF-Token": pm_sess.csrf_token},
            )
            assert t_resp.status_code == 500

        # Verify that task was NOT persisted
        with SessionLocal() as db:
            task = db.query(Task).filter_by(title="Synthetic Rollback Task").first()
            assert task is None, "Task creation should have been rolled back on audit failure"

        # 4. Create safe task, then simulate failure during status transition audit
        t_safe_resp = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={"title": "Synthetic Transition Rollback Task"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert t_safe_resp.status_code == 201
        t_id = t_safe_resp.json()["id"]

        with patch(
            "app.projects.service.record_audit_event",
            side_effect=RuntimeError("Simulated status audit crash"),
        ):
            patch_resp = client.patch(
                f"/api/v1/tasks/{t_id}/status",
                json={"status": "in_progress"},
                headers={"X-CSRF-Token": pm_sess.csrf_token},
            )
            assert patch_resp.status_code == 500

        # Verify task status was rolled back to 'open'
        with SessionLocal() as db:
            persisted_task = db.query(Task).filter_by(id=t_id).first()
            assert persisted_task.status == "open", (
                "Task status transition should have rolled back to open"
            )
    finally:
        engine.dispose()
