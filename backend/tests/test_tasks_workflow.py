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


def create_user_with_roles_and_session(
    db,
    settings,
    user_id: str,
    email: str,
    roles: list[Role],
    is_active: bool = True,
    department: str | None = None,
):
    user = User(
        id=user_id,
        sub=f"sub_{user_id}",
        email=email,
        name=f"User {user_id}",
        is_active=is_active,
        department=department,
    )
    db.add(user)
    for r in roles:
        user_role = UserRole(
            id=f"ur_{user_id}_{r.value}",
            user_id=user.id,
            role=r.value,
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


def test_http_authorization_matrix_tasks_ac17():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        from app.projects.models import ProjectMember, utc_now

        with SessionLocal() as db:
            pm1, s_pm1 = create_user_with_roles_and_session(
                db, settings, "u-t-pm1", "pm1t@corp.local", [Role.PROJECT_MANAGER]
            )
            pm2, s_pm2 = create_user_with_roles_and_session(
                db, settings, "u-t-pm2", "pm2t@corp.local", [Role.PROJECT_MANAGER]
            )
            mem1, s_mem1 = create_user_with_roles_and_session(
                db, settings, "u-t-mem1", "mem1t@corp.local", [Role.MEMBER]
            )
            mem2, s_mem2 = create_user_with_roles_and_session(
                db, settings, "u-t-mem2", "mem2t@corp.local", [Role.MEMBER]
            )
            aud1, s_aud1 = create_user_with_roles_and_session(
                db, settings, "u-t-aud1", "aud1t@corp.local", [Role.AUDITOR]
            )
            admin1, s_admin1 = create_user_with_roles_and_session(
                db, settings, "u-t-admin1", "admin1t@corp.local", [Role.SYSTEM_ADMIN]
            )
            sa_pm, s_sa_pm = create_user_with_roles_and_session(
                db,
                settings,
                "u-t-sapm",
                "sapmt@corp.local",
                [Role.SYSTEM_ADMIN, Role.PROJECT_MANAGER],
            )
            pm_mem, s_pm_mem = create_user_with_roles_and_session(
                db, settings, "u-t-pmmem", "pmmemt@corp.local", [Role.PROJECT_MANAGER, Role.MEMBER]
            )
            pm_aud, s_pm_aud = create_user_with_roles_and_session(
                db, settings, "u-t-pmaud", "pmaudt@corp.local", [Role.PROJECT_MANAGER, Role.AUDITOR]
            )
            mem_aud, s_mem_aud = create_user_with_roles_and_session(
                db, settings, "u-t-memaud", "memaudt@corp.local", [Role.MEMBER, Role.AUDITOR]
            )
            unassigned, s_unassigned = create_user_with_roles_and_session(
                db, settings, "u-t-unassigned", "unassignedt@corp.local", [Role.PROJECT_MANAGER]
            )
            dept_only, s_dept_only = create_user_with_roles_and_session(
                db, settings, "u-t-dept", "deptt@corp.local", [Role.MEMBER], department="dept-p1"
            )

        client = TestClient(app)

        # PM1 creates Project 1
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        r_p1 = client.post(
            "/api/v1/projects",
            json={"name": "P1 for Tasks", "lead_department_id": "dept-p1"},
            headers={"X-CSRF-Token": s_pm1.csrf_token},
        )
        assert r_p1.status_code == 201
        p1_id = r_p1.json()["id"]

        # PM2 creates Project 2
        client.cookies.set(settings.session_cookie_name, s_pm2.id)
        r_p2 = client.post(
            "/api/v1/projects",
            json={"name": "P2 for Tasks", "lead_department_id": "dept-p2"},
            headers={"X-CSRF-Token": s_pm2.csrf_token},
        )
        assert r_p2.status_code == 201
        assert r_p2.json()["id"] is not None

        # Seed memberships on P1
        with SessionLocal() as db:
            now = utc_now()
            db.add_all(
                [
                    ProjectMember(
                        id="pm-t-mem1",
                        project_id=p1_id,
                        user_id=mem1.id,
                        role="member",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-t-mem2",
                        project_id=p1_id,
                        user_id=mem2.id,
                        role="member",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-t-aud1",
                        project_id=p1_id,
                        user_id=aud1.id,
                        role="auditor",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-t-admin1",
                        project_id=p1_id,
                        user_id=admin1.id,
                        role="project_manager",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-t-sapm",
                        project_id=p1_id,
                        user_id=sa_pm.id,
                        role="project_manager",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-t-pmmem",
                        project_id=p1_id,
                        user_id=pm_mem.id,
                        role="member",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-t-pmaud",
                        project_id=p1_id,
                        user_id=pm_aud.id,
                        role="auditor",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-t-memaud",
                        project_id=p1_id,
                        user_id=mem_aud.id,
                        role="member",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                ]
            )
            db.commit()

        # 1. POST /api/v1/projects/{project_id}/tasks
        # PM in scope creates task assigned to mem1
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        r_create_task = client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Task 1", "assignee_id": mem1.id},
            headers={"X-CSRF-Token": s_pm1.csrf_token},
        )
        assert r_create_task.status_code == 201
        t1_id = r_create_task.json()["id"]

        # PM in scope creates unassigned task
        r_create_task2 = client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Task 2"},
            headers={"X-CSRF-Token": s_pm1.csrf_token},
        )
        assert r_create_task2.status_code == 201
        t2_id = r_create_task2.json()["id"]

        # Cross-project PM2 / unassigned PM -> 404
        client.cookies.set(settings.session_cookie_name, s_pm2.id)
        assert (
            client.post(
                f"/api/v1/projects/{p1_id}/tasks",
                json={"title": "Cross Project Task"},
                headers={"X-CSRF-Token": s_pm2.csrf_token},
            ).status_code
            == 404
        )

        client.cookies.set(settings.session_cookie_name, s_unassigned.id)
        assert (
            client.post(
                f"/api/v1/projects/{p1_id}/tasks",
                json={"title": "Unassigned PM Task"},
                headers={"X-CSRF-Token": s_unassigned.csrf_token},
            ).status_code
            == 404
        )

        # Non-PM and multi-role in scope cannot create task -> 403
        for s_user in (s_mem1, s_aud1, s_admin1, s_sa_pm, s_pm_mem, s_pm_aud, s_mem_aud):
            client.cookies.set(settings.session_cookie_name, s_user.id)
            assert (
                client.post(
                    f"/api/v1/projects/{p1_id}/tasks",
                    json={"title": "Forbidden Task"},
                    headers={"X-CSRF-Token": s_user.csrf_token},
                ).status_code
                == 403
            )

        # 2. GET /api/v1/projects/{project_id}/tasks
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        assert len(client.get(f"/api/v1/projects/{p1_id}/tasks").json()) == 2

        client.cookies.set(settings.session_cookie_name, s_mem1.id)
        assert len(client.get(f"/api/v1/projects/{p1_id}/tasks").json()) == 2

        client.cookies.set(settings.session_cookie_name, s_pm_mem.id)
        assert len(client.get(f"/api/v1/projects/{p1_id}/tasks").json()) == 2

        for s_user in (s_aud1, s_admin1, s_sa_pm, s_pm_aud, s_mem_aud, s_unassigned, s_dept_only):
            client.cookies.set(settings.session_cookie_name, s_user.id)
            assert client.get(f"/api/v1/projects/{p1_id}/tasks").status_code == 404

        # 3. GET /api/v1/tasks/{task_id}
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        assert client.get(f"/api/v1/tasks/{t1_id}").status_code == 200

        client.cookies.set(settings.session_cookie_name, s_mem1.id)
        assert client.get(f"/api/v1/tasks/{t1_id}").status_code == 200

        client.cookies.set(settings.session_cookie_name, s_pm_mem.id)
        assert client.get(f"/api/v1/tasks/{t1_id}").status_code == 200

        for s_user in (s_aud1, s_admin1, s_sa_pm, s_pm_aud, s_mem_aud, s_unassigned, s_dept_only):
            client.cookies.set(settings.session_cookie_name, s_user.id)
            assert client.get(f"/api/v1/tasks/{t1_id}").status_code == 404

        # 4. PATCH /api/v1/tasks/{task_id}/status
        # Unassigned / cross-project PM -> 404
        client.cookies.set(settings.session_cookie_name, s_pm2.id)
        assert (
            client.patch(
                f"/api/v1/tasks/{t1_id}/status",
                json={"status": "in_progress"},
                headers={"X-CSRF-Token": s_pm2.csrf_token},
            ).status_code
            == 404
        )

        client.cookies.set(settings.session_cookie_name, s_unassigned.id)
        assert (
            client.patch(
                f"/api/v1/tasks/{t1_id}/status",
                json={"status": "in_progress"},
                headers={"X-CSRF-Token": s_unassigned.csrf_token},
            ).status_code
            == 404
        )

        # Member 2 (not assignee of t1) tries transition -> 403
        client.cookies.set(settings.session_cookie_name, s_mem2.id)
        assert (
            client.patch(
                f"/api/v1/tasks/{t1_id}/status",
                json={"status": "in_progress"},
                headers={"X-CSRF-Token": s_mem2.csrf_token},
            ).status_code
            == 403
        )

        # Member 1 tries PM transition (cancelled) on own task -> 403
        client.cookies.set(settings.session_cookie_name, s_mem1.id)
        assert (
            client.patch(
                f"/api/v1/tasks/{t1_id}/status",
                json={"status": "cancelled"},
                headers={"X-CSRF-Token": s_mem1.csrf_token},
            ).status_code
            == 403
        )

        # Auditor, System Admin, Multi-role cannot transition -> 403
        for s_user in (s_aud1, s_admin1, s_sa_pm, s_pm_mem, s_pm_aud, s_mem_aud):
            client.cookies.set(settings.session_cookie_name, s_user.id)
            assert (
                client.patch(
                    f"/api/v1/tasks/{t1_id}/status",
                    json={"status": "in_progress"},
                    headers={"X-CSRF-Token": s_user.csrf_token},
                ).status_code
                == 403
            )

        # Member 1 transitions own task using ordinary transition (open -> in_progress) -> 200
        client.cookies.set(settings.session_cookie_name, s_mem1.id)
        r_mem_trans = client.patch(
            f"/api/v1/tasks/{t1_id}/status",
            json={"status": "in_progress"},
            headers={"X-CSRF-Token": s_mem1.csrf_token},
        )
        assert r_mem_trans.status_code == 200
        assert r_mem_trans.json()["status"] == "in_progress"

        # PM1 transitions t2 (open -> cancelled) using PM transition -> 200
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        r_pm_trans = client.patch(
            f"/api/v1/tasks/{t2_id}/status",
            json={"status": "cancelled"},
            headers={"X-CSRF-Token": s_pm1.csrf_token},
        )
        assert r_pm_trans.status_code == 200
        assert r_pm_trans.json()["status"] == "cancelled"
    finally:
        engine.dispose()


def test_empty_global_roles_deny_task_endpoints():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm1, s_pm1 = create_user_with_roles_and_session(
                db, settings, "u-teg-pm1", "teg-pm1@corp.local", [Role.PROJECT_MANAGER]
            )
            u_empty, s_empty = create_user_and_session(
                db, settings, "u-teg-empty", "teg-empty@corp.local", role=None
            )
            u_revoke, s_revoke = create_user_with_roles_and_session(
                db, settings, "u-teg-revoke", "teg-revoke@corp.local", [Role.MEMBER]
            )

        client = TestClient(app)

        # PM1 creates Project 1
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        r_p1 = client.post(
            "/api/v1/projects",
            json={"name": "P1 for Task Empty Roles", "lead_department_id": "dept-teg"},
            headers={"X-CSRF-Token": s_pm1.csrf_token},
        )
        assert r_p1.status_code == 201
        p1_id = r_p1.json()["id"]

        # Assign members to Project 1
        with SessionLocal() as db:
            from app.projects.models import ProjectMember

            db.add_all(
                [
                    ProjectMember(
                        id="pm-teg-empty",
                        project_id=p1_id,
                        user_id=u_empty.id,
                        role="member",
                        assigned_by=pm1.id,
                    ),
                    ProjectMember(
                        id="pm-teg-revoke",
                        project_id=p1_id,
                        user_id=u_revoke.id,
                        role="member",
                        assigned_by=pm1.id,
                    ),
                ]
            )
            db.commit()

        # PM creates a task assigned to u_empty
        r_t1 = client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Task Empty", "assignee_id": u_empty.id},
            headers={"X-CSRF-Token": s_pm1.csrf_token},
        )
        assert r_t1.status_code == 201
        t1_id = r_t1.json()["id"]

        # PM creates a task assigned to u_revoke
        r_t2 = client.post(
            f"/api/v1/projects/{p1_id}/tasks",
            json={"title": "Task Revoke", "assignee_id": u_revoke.id},
            headers={"X-CSRF-Token": s_pm1.csrf_token},
        )
        assert r_t2.status_code == 201
        t2_id = r_t2.json()["id"]

        # 1. User with zero global roles is denied across all task endpoints
        client.cookies.set(settings.session_cookie_name, s_empty.id)
        assert (
            client.post(
                f"/api/v1/projects/{p1_id}/tasks",
                json={"title": "Task Prohibited"},
                headers={"X-CSRF-Token": s_empty.csrf_token},
            ).status_code
            == 403
        )
        assert client.get(f"/api/v1/projects/{p1_id}/tasks").status_code == 404
        assert client.get(f"/api/v1/tasks/{t1_id}").status_code == 404
        assert (
            client.patch(
                f"/api/v1/tasks/{t1_id}/status",
                json={"status": "in_progress"},
                headers={"X-CSRF-Token": s_empty.csrf_token},
            ).status_code
            == 403
        )

        # 2. Member before revocation can read tasks and update own task
        client.cookies.set(settings.session_cookie_name, s_revoke.id)
        assert client.get(f"/api/v1/projects/{p1_id}/tasks").status_code == 200
        assert client.get(f"/api/v1/tasks/{t2_id}").status_code == 200

        # Revoke user's global role
        with SessionLocal() as db:
            db.query(UserRole).filter_by(user_id=u_revoke.id).delete()
            db.commit()

        # Subsequent reads and status transitions deny
        assert client.get(f"/api/v1/projects/{p1_id}/tasks").status_code == 404
        assert client.get(f"/api/v1/tasks/{t2_id}").status_code == 404
        assert (
            client.patch(
                f"/api/v1/tasks/{t2_id}/status",
                json={"status": "in_progress"},
                headers={"X-CSRF-Token": s_revoke.csrf_token},
            ).status_code
            == 403
        )
    finally:
        engine.dispose()
