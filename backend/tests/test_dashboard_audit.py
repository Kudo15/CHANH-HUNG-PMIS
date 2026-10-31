import base64
import json
from datetime import datetime, timedelta, timezone

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
from app.projects.models import AuditEvent, Project, ProjectMember, Task, utc_now
from app.projects.schemas import TaskStatus
from app.projects.service import is_task_overdue


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


def create_user_and_session(
    db, settings, user_id: str, email: str, role: Role | None = None, is_active: bool = True
):
    user = User(
        id=user_id,
        sub=f"sub_{user_id}",
        email=email,
        name=f"User {user_id}",
        is_active=is_active,
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


# ============================================================================
# AC-11 Centralized Overdue Unit Tests
# ============================================================================


def test_is_task_overdue_centralized_definition():
    frozen_now = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Null due_date is not overdue
    assert not is_task_overdue(None, TaskStatus.OPEN.value, as_of=frozen_now)

    # 2. Terminal states (done, cancelled) are never overdue even if past due_date
    past_due = frozen_now - timedelta(days=1)
    assert not is_task_overdue(past_due, TaskStatus.DONE.value, as_of=frozen_now)
    assert not is_task_overdue(past_due, TaskStatus.CANCELLED.value, as_of=frozen_now)

    # 3. Active states past due_date are overdue
    assert is_task_overdue(past_due, TaskStatus.OPEN.value, as_of=frozen_now)
    assert is_task_overdue(past_due, TaskStatus.IN_PROGRESS.value, as_of=frozen_now)
    assert is_task_overdue(past_due, TaskStatus.BLOCKED.value, as_of=frozen_now)

    # 4. Due date in future is not overdue
    future_due = frozen_now + timedelta(days=1)
    assert not is_task_overdue(future_due, TaskStatus.OPEN.value, as_of=frozen_now)
    assert not is_task_overdue(future_due, TaskStatus.IN_PROGRESS.value, as_of=frozen_now)

    # 5. Exact boundary: due_date == as_of is not strictly earlier, so not overdue
    assert not is_task_overdue(frozen_now, TaskStatus.OPEN.value, as_of=frozen_now)


# ============================================================================
# AC-11 Dashboard Summary Integration Tests
# ============================================================================


def test_dashboard_summary_unauthenticated_fails_ac11():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        client = TestClient(app)
        resp = client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401
    finally:
        engine.dispose()


def test_dashboard_summary_no_project_assignments_empty_ac11():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            # User with no project memberships
            user, session = create_user_and_session(
                db, settings, "user-no-proj", "noproj@example.com", Role.MEMBER
            )
            # Create another project that this user is NOT member of
            p = Project(
                id="proj-unrelated",
                name="Unrelated Project",
                project_manager_id="pm-other",
                lifecycle="active",
            )
            db.add(p)
            t = Task(
                id="task-unrelated",
                project_id="proj-unrelated",
                title="Task for unrelated project",
                creator_id="pm-other",
                status=TaskStatus.OPEN.value,
            )
            db.add(t)
            db.commit()
            session_id = session.id

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, session_id)

        resp = client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_projects"] == 0
        assert data["total_tasks"] == 0
        assert data["total_overdue_tasks"] == 0
        assert data["projects"] == []
        assert data["total_task_status_counts"] == {
            "open": 0,
            "in_progress": 0,
            "blocked": 0,
            "done": 0,
            "cancelled": 0,
        }
    finally:
        engine.dispose()


def test_dashboard_summary_scoped_to_assigned_projects_ac11():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            user, session = create_user_and_session(
                db, settings, "u1", "u1@example.com", Role.PROJECT_MANAGER
            )
            session_id = session.id

            # Project 1: User is assigned as PM
            p1 = Project(id="p1", name="Project One", project_manager_id="u1", lifecycle="active")
            db.add(p1)
            pm1 = ProjectMember(
                id="pm1", project_id="p1", user_id="u1", role="project_manager", assigned_by="u1"
            )
            db.add(pm1)

            # Project 2: User is NOT assigned
            p2 = Project(
                id="p2", name="Project Two", project_manager_id="pm-other", lifecycle="active"
            )
            db.add(p2)
            pm2 = ProjectMember(
                id="pm2",
                project_id="p2",
                user_id="pm-other",
                role="project_manager",
                assigned_by="pm-other",
            )
            db.add(pm2)

            now = utc_now()
            # Tasks for Project 1 (User's project)
            # 1 overdue open task
            t1 = Task(
                id="t1",
                project_id="p1",
                title="P1 Task 1",
                creator_id="u1",
                status=TaskStatus.OPEN.value,
                due_date=now - timedelta(days=2),
            )
            # 1 in_progress future task
            t2 = Task(
                id="t2",
                project_id="p1",
                title="P1 Task 2",
                creator_id="u1",
                status=TaskStatus.IN_PROGRESS.value,
                due_date=now + timedelta(days=3),
            )
            # 1 done overdue task (terminal: should not count as overdue)
            t3 = Task(
                id="t3",
                project_id="p1",
                title="P1 Task 3",
                creator_id="u1",
                status=TaskStatus.DONE.value,
                due_date=now - timedelta(days=5),
            )
            db.add_all([t1, t2, t3])

            # Tasks for Project 2 (Unauthorized project - must NOT leak into dashboard)
            t_other1 = Task(
                id="t_other1",
                project_id="p2",
                title="P2 Task 1",
                creator_id="pm-other",
                status=TaskStatus.OPEN.value,
                due_date=now - timedelta(days=10),
            )
            t_other2 = Task(
                id="t_other2",
                project_id="p2",
                title="P2 Task 2",
                creator_id="pm-other",
                status=TaskStatus.BLOCKED.value,
                due_date=now - timedelta(days=10),
            )
            db.add_all([t_other1, t_other2])
            db.commit()

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, session_id)

        resp = client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()

        # Only Project 1 must appear
        assert data["total_projects"] == 1
        assert len(data["projects"]) == 1
        p_item = data["projects"][0]
        assert p_item["project_id"] == "p1"
        assert p_item["project_name"] == "Project One"
        assert p_item["total_task_count"] == 3
        assert p_item["overdue_task_count"] == 1  # only t1 is overdue
        assert p_item["task_status_counts"] == {
            "open": 1,
            "in_progress": 1,
            "blocked": 0,
            "done": 1,
            "cancelled": 0,
        }

        # Totals match only Project 1
        assert data["total_tasks"] == 3
        assert data["total_overdue_tasks"] == 1
        assert data["total_task_status_counts"] == {
            "open": 1,
            "in_progress": 1,
            "blocked": 0,
            "done": 1,
            "cancelled": 0,
        }
    finally:
        engine.dispose()


def test_dashboard_task_status_counts_all_states_and_overdue_boundary_ac11():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            user, session = create_user_and_session(
                db, settings, "u-all", "all@example.com", Role.MEMBER
            )
            session_id = session.id

            p = Project(
                id="p-all", name="All States Proj", project_manager_id="pm-all", lifecycle="active"
            )
            db.add(p)
            pm = ProjectMember(
                id="pm-all",
                project_id="p-all",
                user_id="u-all",
                role="member",
                assigned_by="pm-all",
            )
            db.add(pm)

            now = utc_now()
            # 5 tasks covering all 5 statuses
            tasks = [
                Task(
                    id="t-open",
                    project_id="p-all",
                    title="Open",
                    creator_id="u-all",
                    status=TaskStatus.OPEN.value,
                    due_date=now - timedelta(days=1),
                ),
                Task(
                    id="t-in-progress",
                    project_id="p-all",
                    title="InProg",
                    creator_id="u-all",
                    status=TaskStatus.IN_PROGRESS.value,
                    due_date=now - timedelta(days=1),
                ),
                Task(
                    id="t-blocked",
                    project_id="p-all",
                    title="Blocked",
                    creator_id="u-all",
                    status=TaskStatus.BLOCKED.value,
                    due_date=now - timedelta(days=1),
                ),
                Task(
                    id="t-done",
                    project_id="p-all",
                    title="Done",
                    creator_id="u-all",
                    status=TaskStatus.DONE.value,
                    due_date=now - timedelta(days=1),
                ),
                Task(
                    id="t-cancelled",
                    project_id="p-all",
                    title="Cancelled",
                    creator_id="u-all",
                    status=TaskStatus.CANCELLED.value,
                    due_date=now - timedelta(days=1),
                ),
            ]
            db.add_all(tasks)
            db.commit()

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, session_id)

        resp = client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_tasks"] == 5
        # Out of 5 past-due tasks, done and cancelled are excluded -> exactly 3 overdue
        assert data["total_overdue_tasks"] == 3
        assert data["total_task_status_counts"] == {
            "open": 1,
            "in_progress": 1,
            "blocked": 1,
            "done": 1,
            "cancelled": 1,
        }
    finally:
        engine.dispose()


def test_dashboard_summary_is_read_only_ac11():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            user, session = create_user_and_session(
                db, settings, "u-ro", "ro@example.com", Role.MEMBER
            )
            session_id = session.id
            p = Project(id="p-ro", name="RO Project", project_manager_id="u-ro", lifecycle="active")
            db.add(p)
            db.add(
                ProjectMember(
                    id="pm-ro", project_id="p-ro", user_id="u-ro", role="member", assigned_by="u-ro"
                )
            )
            db.commit()

            initial_audits_count = db.query(AuditEvent).count()
            initial_tasks_count = db.query(Task).count()

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, session_id)

        resp = client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200

        with SessionLocal() as db:
            assert db.query(AuditEvent).count() == initial_audits_count
            assert db.query(Task).count() == initial_tasks_count
    finally:
        engine.dispose()


# ============================================================================
# AC-12 & AC-13 Project-Scoped Audit History Tests
# ============================================================================


def test_audit_read_by_in_scope_project_manager_and_auditor_succeeds_ac12_ac13():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            # Create Project Manager
            pm, pm_session = create_user_and_session(
                db, settings, "pm-audit", "pm-audit@example.com", Role.PROJECT_MANAGER
            )
            # Create Auditor
            auditor, aud_session = create_user_and_session(
                db, settings, "aud-user", "auditor@example.com", Role.AUDITOR
            )

            p = Project(
                id="p-audited",
                name="Audited Project",
                project_manager_id="pm-audit",
                lifecycle="active",
            )
            db.add(p)

            # Assign PM as project_manager
            db.add(
                ProjectMember(
                    id="pm-m1",
                    project_id="p-audited",
                    user_id="pm-audit",
                    role="project_manager",
                    assigned_by="pm-audit",
                )
            )
            # Assign Auditor as auditor
            db.add(
                ProjectMember(
                    id="pm-m2",
                    project_id="p-audited",
                    user_id="aud-user",
                    role="auditor",
                    assigned_by="pm-audit",
                )
            )

            # Create an audit event for this project
            event = AuditEvent(
                id="ae-1",
                actor_id="pm-audit",
                action="project:create",
                target_type="project",
                target_id="p-audited",
                project_id="p-audited",
                correlation_id="corr-1",
                before_values=None,
                after_values={"lifecycle": "active", "lead_department_id": "dept-1"},
                created_at=utc_now(),
            )
            db.add(event)
            db.commit()

            pm_session_id = pm_session.id
            aud_session_id = aud_session.id

        client = TestClient(app)

        # 1. Project Manager in scope can read
        client.cookies.set(settings.session_cookie_name, pm_session_id)
        resp_pm = client.get("/api/v1/projects/p-audited/audit-events")
        assert resp_pm.status_code == 200
        data_pm = resp_pm.json()
        assert len(data_pm["items"]) == 1
        assert data_pm["items"][0]["id"] == "ae-1"
        assert data_pm["items"][0]["actor_id"] == "pm-audit"
        assert data_pm["items"][0]["action"] == "project:create"

        # 2. Auditor in scope can read
        client.cookies.set(settings.session_cookie_name, aud_session_id)
        resp_aud = client.get("/api/v1/projects/p-audited/audit-events")
        assert resp_aud.status_code == 200
        data_aud = resp_aud.json()
        assert len(data_aud["items"]) == 1
        assert data_aud["items"][0]["id"] == "ae-1"
    finally:
        engine.dispose()


def test_audit_read_forbidden_and_non_disclosing_matrix_ac13():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_session = create_user_and_session(
                db, settings, "pm-owner", "pm-owner@example.com", Role.PROJECT_MANAGER
            )
            member, member_session = create_user_and_session(
                db, settings, "mem-user", "mem@example.com", Role.MEMBER
            )
            sys_admin, admin_session = create_user_and_session(
                db, settings, "admin-user", "admin@example.com", Role.SYSTEM_ADMIN
            )
            other_pm, other_pm_session = create_user_and_session(
                db, settings, "pm-other", "other@example.com", Role.PROJECT_MANAGER
            )
            inactive_user, inactive_session = create_user_and_session(
                db, settings, "inactive-user", "inactive@example.com", Role.AUDITOR, is_active=False
            )

            p1 = Project(
                id="p-secret", name="Secret Proj", project_manager_id="pm-owner", lifecycle="active"
            )
            db.add(p1)
            # member is assigned as Member (not PM or Auditor)
            db.add(
                ProjectMember(
                    id="pm-sec-owner",
                    project_id="p-secret",
                    user_id="pm-owner",
                    role="project_manager",
                    assigned_by="pm-owner",
                )
            )
            db.add(
                ProjectMember(
                    id="pm-sec-mem",
                    project_id="p-secret",
                    user_id="mem-user",
                    role="member",
                    assigned_by="pm-owner",
                )
            )

            # other_pm is assigned to a different project
            p2 = Project(
                id="p-other", name="Other Proj", project_manager_id="pm-other", lifecycle="active"
            )
            db.add(p2)
            db.add(
                ProjectMember(
                    id="pm-other-m",
                    project_id="p-other",
                    user_id="pm-other",
                    role="project_manager",
                    assigned_by="pm-other",
                )
            )

            # Audit event on p-secret
            db.add(
                AuditEvent(
                    id="ae-secret",
                    actor_id="pm-owner",
                    action="project:create",
                    target_type="project",
                    target_id="p-secret",
                    project_id="p-secret",
                    correlation_id="corr-sec",
                    created_at=utc_now(),
                )
            )
            db.commit()

        client = TestClient(app)

        # 1. Unauthenticated -> 401
        resp = client.get("/api/v1/projects/p-secret/audit-events")
        assert resp.status_code == 401

        # 2. Inactive user -> 403 (inactive/deprovisioned user fails closed)
        client.cookies.set(settings.session_cookie_name, inactive_session.id)
        resp = client.get("/api/v1/projects/p-secret/audit-events")
        assert resp.status_code == 403

        # 3. Member assigned to project -> 404 (non-disclosing fail-closed)
        client.cookies.set(settings.session_cookie_name, member_session.id)
        resp = client.get("/api/v1/projects/p-secret/audit-events")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Project not found"

        # 4. System Admin without explicit project assignment -> 404
        client.cookies.set(settings.session_cookie_name, admin_session.id)
        resp = client.get("/api/v1/projects/p-secret/audit-events")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Project not found"

        # 5. Cross-project PM (PM of p-other accessing p-secret) -> 404
        client.cookies.set(settings.session_cookie_name, other_pm_session.id)
        resp = client.get("/api/v1/projects/p-secret/audit-events")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Project not found"

        # 6. Guessed non-existent project ID -> 404
        client.cookies.set(settings.session_cookie_name, pm_session.id)
        resp = client.get("/api/v1/projects/guessed-project-9999/audit-events")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Project not found"
    finally:
        engine.dispose()


def test_audit_events_safe_field_allowlist_excludes_secrets_and_freeform_ac12():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, session = create_user_and_session(
                db, settings, "pm-allowlist", "al@example.com", Role.PROJECT_MANAGER
            )
            p = Project(
                id="p-al", name="AL Proj", project_manager_id="pm-allowlist", lifecycle="active"
            )
            db.add(p)
            db.add(
                ProjectMember(
                    id="pm-al-mem",
                    project_id="p-al",
                    user_id="pm-allowlist",
                    role="project_manager",
                    assigned_by="pm-allowlist",
                )
            )

            # Even if raw DB contains forbidden keys (e.g. description, title, password, token)
            # the read path must strip and exclude them!
            unsafe_event = AuditEvent(
                id="ae-unsafe",
                actor_id="pm-allowlist",
                action="task:create",
                target_type="task",
                target_id="t-100",
                project_id="p-al",
                correlation_id="corr-al",
                before_values=None,
                after_values={
                    "status": "open",
                    "due_date": "2026-11-01T00:00:00Z",
                    "title": "Forbidden Title Secret",
                    "description": "Forbidden Description Text",
                    "password": "super_secret_password",
                    "token": "bearer_xyz",
                },
                created_at=utc_now(),
            )
            db.add(unsafe_event)
            db.commit()
            session_id = session.id

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, session_id)

        resp = client.get("/api/v1/projects/p-al/audit-events")
        assert resp.status_code == 200
        data = resp.json()
        item = data["items"][0]

        # Verify allowed metadata
        assert item["id"] == "ae-unsafe"
        assert item["actor_id"] == "pm-allowlist"
        assert item["action"] == "task:create"
        assert item["target_type"] == "task"
        assert item["target_id"] == "t-100"
        assert item["project_id"] == "p-al"
        assert item["correlation_id"] == "corr-al"
        assert "created_at" in item

        # Verify allowlisted values ONLY
        after = item["after_values"]
        assert "status" in after
        assert "due_date" in after
        assert "title" not in after
        assert "description" not in after
        assert "password" not in after
        assert "token" not in after
    finally:
        engine.dispose()


def test_audit_events_stable_newest_first_and_cursor_pagination_ac12():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        base_time = datetime(2026, 10, 30, 10, 0, 0, tzinfo=timezone.utc)
        with SessionLocal() as db:
            pm, session = create_user_and_session(
                db, settings, "pm-page", "page@example.com", Role.PROJECT_MANAGER
            )
            p = Project(
                id="p-page", name="Page Proj", project_manager_id="pm-page", lifecycle="active"
            )
            db.add(p)
            db.add(
                ProjectMember(
                    id="pm-p-mem",
                    project_id="p-page",
                    user_id="pm-page",
                    role="project_manager",
                    assigned_by="pm-page",
                )
            )

            # Create 5 audit events with strictly ascending timestamps
            for i in range(1, 6):
                db.add(
                    AuditEvent(
                        id=f"ae-{i}",
                        actor_id="pm-page",
                        action=f"action:{i}",
                        target_type="project",
                        target_id="p-page",
                        project_id="p-page",
                        correlation_id=f"corr-{i}",
                        created_at=base_time + timedelta(minutes=i),
                    )
                )
            db.commit()
            session_id = session.id

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, session_id)

        # Page 1: limit 2 -> should return ae-5 and ae-4 (newest first)
        resp1 = client.get("/api/v1/projects/p-page/audit-events?limit=2")
        assert resp1.status_code == 200
        d1 = resp1.json()
        assert len(d1["items"]) == 2
        assert [x["id"] for x in d1["items"]] == ["ae-5", "ae-4"]
        assert d1["has_more"] is True
        assert d1["next_cursor"] is not None
        cursor1 = d1["next_cursor"]

        # Page 2: use cursor1, limit 2 -> should return ae-3 and ae-2
        resp2 = client.get(f"/api/v1/projects/p-page/audit-events?limit=2&cursor={cursor1}")
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert len(d2["items"]) == 2
        assert [x["id"] for x in d2["items"]] == ["ae-3", "ae-2"]
        assert d2["has_more"] is True
        assert d2["next_cursor"] is not None
        cursor2 = d2["next_cursor"]

        # Page 3: use cursor2, limit 2 -> should return ae-1
        resp3 = client.get(f"/api/v1/projects/p-page/audit-events?limit=2&cursor={cursor2}")
        assert resp3.status_code == 200
        d3 = resp3.json()
        assert len(d3["items"]) == 1
        assert [x["id"] for x in d3["items"]] == ["ae-1"]
        assert d3["has_more"] is False
        assert d3["next_cursor"] is None
    finally:
        engine.dispose()


def test_audit_cursor_tampering_and_cross_project_reuse_fails_ac12():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, session = create_user_and_session(
                db, settings, "pm-cur", "cur@example.com", Role.PROJECT_MANAGER
            )
            p1 = Project(
                id="p-cur-1", name="Cur Proj 1", project_manager_id="pm-cur", lifecycle="active"
            )
            p2 = Project(
                id="p-cur-2", name="Cur Proj 2", project_manager_id="pm-cur", lifecycle="active"
            )
            db.add_all([p1, p2])
            db.add(
                ProjectMember(
                    id="pm-c1",
                    project_id="p-cur-1",
                    user_id="pm-cur",
                    role="project_manager",
                    assigned_by="pm-cur",
                )
            )
            db.add(
                ProjectMember(
                    id="pm-c2",
                    project_id="p-cur-2",
                    user_id="pm-cur",
                    role="project_manager",
                    assigned_by="pm-cur",
                )
            )

            # Audit events
            db.add(
                AuditEvent(
                    id="ae-c1",
                    actor_id="pm-cur",
                    action="a:1",
                    target_type="project",
                    target_id="p-cur-1",
                    project_id="p-cur-1",
                    correlation_id="c-1",
                    created_at=utc_now(),
                )
            )
            db.add(
                AuditEvent(
                    id="ae-c2",
                    actor_id="pm-cur",
                    action="a:2",
                    target_type="project",
                    target_id="p-cur-1",
                    project_id="p-cur-1",
                    correlation_id="c-2",
                    created_at=utc_now(),
                )
            )
            db.commit()
            session_id = session.id

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, session_id)

        # 1. Fetch valid cursor from project 1
        r = client.get("/api/v1/projects/p-cur-1/audit-events?limit=1")
        assert r.status_code == 200
        valid_cursor_p1 = r.json()["next_cursor"]
        assert valid_cursor_p1 is not None

        # 2. Tampered cursor: corrupted base64 -> 400
        bad_b64 = client.get("/api/v1/projects/p-cur-1/audit-events?cursor=not-valid-base64!")
        assert bad_b64.status_code == 400
        assert "Invalid cursor" in bad_b64.json()["detail"]

        # 3. Tampered cursor: invalid json payload
        corrupted_json = base64.urlsafe_b64encode(b"not json").decode()
        bad_json = client.get(f"/api/v1/projects/p-cur-1/audit-events?cursor={corrupted_json}")
        assert bad_json.status_code == 400
        assert "Invalid cursor" in bad_json.json()["detail"]

        # 4. Tampered cursor: missing required fields
        incomplete_json = base64.urlsafe_b64encode(json.dumps({"foo": "bar"}).encode()).decode()
        bad_fields = client.get(f"/api/v1/projects/p-cur-1/audit-events?cursor={incomplete_json}")
        assert bad_fields.status_code == 400
        assert "Invalid cursor" in bad_fields.json()["detail"]

        # 5. Cross-project cursor reuse: cursor issued for p-cur-1 passed to p-cur-2 -> 400
        cross_proj = client.get(f"/api/v1/projects/p-cur-2/audit-events?cursor={valid_cursor_p1}")
        assert cross_proj.status_code == 400
        assert "Invalid cursor for this project" in cross_proj.json()["detail"]
    finally:
        engine.dispose()


def test_audit_endpoint_bounded_limit_and_read_only_ac12():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, session = create_user_and_session(
                db, settings, "pm-cap", "cap@example.com", Role.PROJECT_MANAGER
            )
            p = Project(
                id="p-cap", name="Cap Proj", project_manager_id="pm-cap", lifecycle="active"
            )
            db.add(p)
            db.add(
                ProjectMember(
                    id="pm-cap-m",
                    project_id="p-cap",
                    user_id="pm-cap",
                    role="project_manager",
                    assigned_by="pm-cap",
                )
            )
            db.add(
                AuditEvent(
                    id="ae-cap",
                    actor_id="pm-cap",
                    action="a:1",
                    target_type="project",
                    target_id="p-cap",
                    project_id="p-cap",
                    correlation_id="c-1",
                    created_at=utc_now(),
                )
            )
            db.commit()
            session_id = session.id
            initial_audit_count = db.query(AuditEvent).count()

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, session_id)

        # Exceeding max limit (100) -> 422 Unprocessable Entity
        r_over = client.get("/api/v1/projects/p-cap/audit-events?limit=101")
        assert r_over.status_code == 422

        # Negative / zero limit -> 422
        r_zero = client.get("/api/v1/projects/p-cap/audit-events?limit=0")
        assert r_zero.status_code == 422

        # Valid read leaves database intact
        r_valid = client.get("/api/v1/projects/p-cap/audit-events?limit=50")
        assert r_valid.status_code == 200
        with SessionLocal() as db:
            assert db.query(AuditEvent).count() == initial_audit_count
    finally:
        engine.dispose()


def test_no_global_audit_endpoint_ac12():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, session = create_user_and_session(
                db, settings, "pm-global", "global@example.com", Role.PROJECT_MANAGER
            )
            session_id = session.id

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, session_id)

        # No global audit collection endpoint must exist
        r1 = client.get("/api/v1/audit-events")
        assert r1.status_code == 404
        r2 = client.get("/api/v1/audit")
        assert r2.status_code == 404
    finally:
        engine.dispose()
