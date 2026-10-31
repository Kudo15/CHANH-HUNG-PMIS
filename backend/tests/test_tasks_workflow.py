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
from app.projects.models import AuditEvent


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


def test_task_create_within_project_and_assignee_validation_ac08():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-task", "pmtask@example.com", Role.PROJECT_MANAGER
            )
            mem, mem_sess = create_user_and_session(
                db, settings, "mem-task", "memtask@example.com", Role.MEMBER
            )
            non_member, non_mem_sess = create_user_and_session(
                db, settings, "outsider", "outsider@example.com", Role.MEMBER
            )

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)

        # 1. PM creates project
        proj_resp = client.post(
            "/api/v1/projects",
            json={"name": "Task Test Project"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        p_id = proj_resp.json()["id"]

        # 2. PM adds mem to project
        client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "mem-task", "role": "member"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )

        # 3. Create task assigned to member -> succeeds
        task_payload = {
            "title": "Synthetic Task Item 101",
            "description": "Synthetic task description for test verification",
            "assignee_id": "mem-task",
            "due_date": "2026-11-15T17:00:00Z",
        }
        create_task_resp = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json=task_payload,
            headers={"X-CSRF-Token": pm_sess.csrf_token, "X-Correlation-ID": "corr-task-01"},
        )
        assert create_task_resp.status_code == 201
        t_data = create_task_resp.json()
        assert t_data["title"] == task_payload["title"]
        assert t_data["description"] == task_payload["description"]
        assert t_data["creator_id"] == "pm-task"
        assert t_data["assignee_id"] == "mem-task"
        assert t_data["status"] == "open"
        t_id = t_data["id"]

        # Verify audit write for task:create (no description in audit)
        with SessionLocal() as db:
            audit = db.query(AuditEvent).filter_by(target_id=t_id, action="task:create").first()
            assert audit is not None
            assert audit.actor_id == "pm-task"
            assert audit.project_id == p_id
            assert "description" not in audit.after_values
            assert "title" not in audit.after_values
            assert audit.after_values["status"] == "open"

        # 4. Create task with assignee NOT in project -> fails closed (400)
        invalid_assignee_resp = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={
                "title": "Task with outsider",
                "assignee_id": "outsider",
            },
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert invalid_assignee_resp.status_code == 400

        # 5. Member cannot create task -> 403
        client.cookies.set(settings.session_cookie_name, mem_sess.id)
        member_create_resp = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={"title": "Member trying to create task"},
            headers={"X-CSRF-Token": mem_sess.csrf_token},
        )
        assert member_create_resp.status_code == 403

        # 6. Outsider cannot create task or view project tasks -> 404
        client.cookies.set(settings.session_cookie_name, non_mem_sess.id)
        outsider_create_resp = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={"title": "Outsider create task"},
            headers={"X-CSRF-Token": non_mem_sess.csrf_token},
        )
        assert outsider_create_resp.status_code == 404

        outsider_list_resp = client.get(f"/api/v1/projects/{p_id}/tasks")
        assert outsider_list_resp.status_code == 404
    finally:
        engine.dispose()


def test_task_transitions_ordinary_work_path_ac09():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-flow", "pmflow@example.com", Role.PROJECT_MANAGER
            )
            mem, mem_sess = create_user_and_session(
                db, settings, "mem-flow", "memflow@example.com", Role.MEMBER
            )

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)

        # Setup project & member & task
        p_resp = client.post(
            "/api/v1/projects",
            json={"name": "Transition Project"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        p_id = p_resp.json()["id"]

        client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "mem-flow", "role": "member"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )

        t_resp = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={"title": "Test Ordinary Transitions", "assignee_id": "mem-flow"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        t_id = t_resp.json()["id"]

        # Switch to Member session
        client.cookies.set(settings.session_cookie_name, mem_sess.id)

        # 1. open -> in_progress (allowed)
        r1 = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "in_progress"},
            headers={"X-CSRF-Token": mem_sess.csrf_token, "X-Correlation-ID": "corr-trans-1"},
        )
        assert r1.status_code == 200
        assert r1.json()["status"] == "in_progress"

        # 2. in_progress -> blocked (allowed)
        r2 = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "blocked"},
            headers={"X-CSRF-Token": mem_sess.csrf_token, "X-Correlation-ID": "corr-trans-2"},
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "blocked"

        # 3. blocked -> in_progress (allowed)
        r3 = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "in_progress"},
            headers={"X-CSRF-Token": mem_sess.csrf_token, "X-Correlation-ID": "corr-trans-3"},
        )
        assert r3.status_code == 200
        assert r3.json()["status"] == "in_progress"

        # 4. in_progress -> done (allowed)
        r4 = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "done"},
            headers={"X-CSRF-Token": mem_sess.csrf_token, "X-Correlation-ID": "corr-trans-4"},
        )
        assert r4.status_code == 200
        assert r4.json()["status"] == "done"

        # 5. Member cannot reopen done -> in_progress (403 forbidden)
        r_reopen_mem = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "in_progress"},
            headers={"X-CSRF-Token": mem_sess.csrf_token},
        )
        assert r_reopen_mem.status_code == 403

        # 6. PM can reopen done -> in_progress (allowed)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)
        r_reopen_pm = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "in_progress"},
            headers={"X-CSRF-Token": pm_sess.csrf_token, "X-Correlation-ID": "corr-reopen-pm"},
        )
        assert r_reopen_pm.status_code == 200
        assert r_reopen_pm.json()["status"] == "in_progress"
    finally:
        engine.dispose()


def test_task_cancellation_and_terminal_state_ac09():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-cancel", "pmcancel@example.com", Role.PROJECT_MANAGER
            )
            mem, mem_sess = create_user_and_session(
                db, settings, "mem-cancel", "memcancel@example.com", Role.MEMBER
            )

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)

        # Project and task setup
        p_id = client.post(
            "/api/v1/projects",
            json={"name": "Cancel Project"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        ).json()["id"]

        client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "mem-cancel", "role": "member"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )

        t_id = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={"title": "Task to Cancel", "assignee_id": "mem-cancel"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        ).json()["id"]

        # 1. Member cannot cancel task (403)
        client.cookies.set(settings.session_cookie_name, mem_sess.id)
        r_mem_cancel = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "cancelled"},
            headers={"X-CSRF-Token": mem_sess.csrf_token},
        )
        assert r_mem_cancel.status_code == 403

        # 2. PM can cancel task (open -> cancelled)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)
        r_pm_cancel = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "cancelled"},
            headers={"X-CSRF-Token": pm_sess.csrf_token, "X-Correlation-ID": "corr-cancel-01"},
        )
        assert r_pm_cancel.status_code == 200
        assert r_pm_cancel.json()["status"] == "cancelled"

        # 3. Cancelled is TERMINAL -> neither PM nor Member can transition out of cancelled (400)
        r_out_cancel = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "in_progress"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert r_out_cancel.status_code == 400

        # 4. Cannot cancel a completed ('done') task
        t2_id = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={"title": "Done Task", "assignee_id": "mem-cancel"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        ).json()["id"]
        # Advance to done
        client.patch(
            f"/api/v1/tasks/{t2_id}/status",
            json={"status": "in_progress"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        client.patch(
            f"/api/v1/tasks/{t2_id}/status",
            json={"status": "done"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        # Attempt cancel on done task -> invalid transition (400)
        r_cancel_done = client.patch(
            f"/api/v1/tasks/{t2_id}/status",
            json={"status": "cancelled"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert r_cancel_done.status_code == 400
    finally:
        engine.dispose()


def test_member_cannot_modify_other_members_task_ac09():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-own", "pmown@example.com", Role.PROJECT_MANAGER
            )
            mem1, mem1_sess = create_user_and_session(
                db, settings, "mem-1", "mem1@example.com", Role.MEMBER
            )
            mem2, mem2_sess = create_user_and_session(
                db, settings, "mem-2", "mem2@example.com", Role.MEMBER
            )

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)

        # Setup project & 2 members
        p_id = client.post(
            "/api/v1/projects",
            json={"name": "Ownership Project"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        ).json()["id"]

        client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "mem-1", "role": "member"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "mem-2", "role": "member"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )

        # Create task assigned to mem-2
        t_id = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={"title": "Member 2's Task", "assignee_id": "mem-2"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        ).json()["id"]

        # Mem1 is in project, so mem1 CAN read the task
        client.cookies.set(settings.session_cookie_name, mem1_sess.id)
        r_read = client.get(f"/api/v1/tasks/{t_id}")
        assert r_read.status_code == 200

        # Mem1 CANNOT update status of mem-2's task -> 403
        r_mutate = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "in_progress"},
            headers={"X-CSRF-Token": mem1_sess.csrf_token},
        )
        assert r_mutate.status_code == 403
    finally:
        engine.dispose()


def test_archived_project_tasks_are_read_only_ac09():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-arc-task", "pmarctask@example.com", Role.PROJECT_MANAGER
            )

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)

        # Project and task setup
        p_id = client.post(
            "/api/v1/projects",
            json={"name": "Archived Task Project"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        ).json()["id"]

        t_id = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={"title": "Task in soon-archived project"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        ).json()["id"]

        # Archive project
        client.post(
            f"/api/v1/projects/{p_id}/archive",
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )

        # Cannot create new tasks in archived project (400)
        r_create = client.post(
            f"/api/v1/projects/{p_id}/tasks",
            json={"title": "New Task after archive"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert r_create.status_code == 400

        # Cannot transition existing task in archived project (400)
        r_trans = client.patch(
            f"/api/v1/tasks/{t_id}/status",
            json={"status": "in_progress"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert r_trans.status_code == 400
    finally:
        engine.dispose()
