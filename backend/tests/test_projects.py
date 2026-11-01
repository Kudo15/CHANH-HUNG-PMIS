from app.auth.models import User, UserRole
from app.auth.policy import Role
from app.auth.session import create_session
from app.config import Settings
from app.database import Base
from app.main import create_app
from app.projects.models import AuditEvent, Project, ProjectMember, Task
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


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
    db,
    settings,
    user_id: str,
    email: str,
    role: Role | None = None,
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


def test_project_create_by_project_manager_succeeds_ac06():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_session = create_user_and_session(
                db, settings, "pm-1", "pm1@example.com", Role.PROJECT_MANAGER
            )
            session_id = pm_session.id
            csrf_token = pm_session.csrf_token

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, session_id)

        # Create project with approved fields
        payload = {
            "name": "Synthetic Sample Project 101",
            "description": "Synthetic test project description for automated suite",
            "lead_department_id": "dept-opaque-01",
            "start_date": "2026-11-01",
            "end_date": "2027-11-01",
        }
        resp = client.post(
            "/api/v1/projects",
            json=payload,
            headers={"X-CSRF-Token": csrf_token, "X-Correlation-ID": "corr-create-01"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert data["lead_department_id"] == "dept-opaque-01"
        assert data["project_manager_id"] == "pm-1"
        assert data["lifecycle"] == "active"
        assert "id" in data
        project_id = data["id"]

        # Verify initial PM is automatically added as project member
        with SessionLocal() as db:
            proj = db.query(Project).filter_by(id=project_id).first()
            assert proj is not None
            assert proj.lifecycle == "active"

            pm_member = (
                db.query(ProjectMember).filter_by(project_id=project_id, user_id="pm-1").first()
            )
            assert pm_member is not None
            assert pm_member.role == "project_manager"

            # Verify audit write
            audit = (
                db.query(AuditEvent)
                .filter_by(target_id=project_id, action="project:create")
                .first()
            )
            assert audit is not None
            assert audit.actor_id == "pm-1"
            assert audit.correlation_id == "corr-create-01"
            assert "description" not in audit.after_values
            assert "name" not in audit.after_values
            assert audit.after_values["lifecycle"] == "active"
    finally:
        engine.dispose()


def test_project_create_forbidden_for_member_and_system_admin():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            _, m_session = create_user_and_session(
                db, settings, "m-1", "m1@example.com", Role.MEMBER
            )
            _, sa_session = create_user_and_session(
                db, settings, "sa-1", "sa1@example.com", Role.SYSTEM_ADMIN
            )

        client = TestClient(app)

        # Member cannot create project
        client.cookies.set(settings.session_cookie_name, m_session.id)
        resp_m = client.post(
            "/api/v1/projects",
            json={"name": "Member Project"},
            headers={"X-CSRF-Token": m_session.csrf_token},
        )
        assert resp_m.status_code == 403

        # System Admin without project_manager role cannot create project
        client.cookies.set(settings.session_cookie_name, sa_session.id)
        resp_sa = client.post(
            "/api/v1/projects",
            json={"name": "Admin Project"},
            headers={"X-CSRF-Token": sa_session.csrf_token},
        )
        assert resp_sa.status_code == 403
    finally:
        engine.dispose()


def test_project_list_and_read_scoped_to_assigned_members_ac06_ac10():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm1, pm1_sess = create_user_and_session(
                db, settings, "pm-1", "pm1@example.com", Role.PROJECT_MANAGER
            )
            pm2, pm2_sess = create_user_and_session(
                db, settings, "pm-2", "pm2@example.com", Role.PROJECT_MANAGER
            )
            mem1, mem1_sess = create_user_and_session(
                db, settings, "mem-1", "mem1@example.com", Role.MEMBER
            )
            admin, admin_sess = create_user_and_session(
                db, settings, "admin-1", "admin@example.com", Role.SYSTEM_ADMIN
            )

        client = TestClient(app)

        # PM1 creates Project 1
        client.cookies.set(settings.session_cookie_name, pm1_sess.id)
        resp = client.post(
            "/api/v1/projects",
            json={"name": "Project Alpha"},
            headers={"X-CSRF-Token": pm1_sess.csrf_token},
        )
        assert resp.status_code == 201
        p1_id = resp.json()["id"]

        # PM2 creates Project 2
        client.cookies.set(settings.session_cookie_name, pm2_sess.id)
        resp = client.post(
            "/api/v1/projects",
            json={"name": "Project Beta"},
            headers={"X-CSRF-Token": pm2_sess.csrf_token},
        )
        assert resp.status_code == 201
        p2_id = resp.json()["id"]

        # PM1 assigns mem1 to Project 1 as member
        client.cookies.set(settings.session_cookie_name, pm1_sess.id)
        resp_assign = client.post(
            f"/api/v1/projects/{p1_id}/members",
            json={"user_id": "mem-1", "role": "member"},
            headers={"X-CSRF-Token": pm1_sess.csrf_token},
        )
        assert resp_assign.status_code == 201

        # 1. PM1 sees only Project 1
        resp_list1 = client.get("/api/v1/projects")
        assert resp_list1.status_code == 200
        p_ids1 = [p["id"] for p in resp_list1.json()]
        assert p_ids1 == [p1_id]
        assert p2_id not in p_ids1

        # 2. PM2 sees only Project 2
        client.cookies.set(settings.session_cookie_name, pm2_sess.id)
        resp_list2 = client.get("/api/v1/projects")
        assert resp_list2.status_code == 200
        p_ids2 = [p["id"] for p in resp_list2.json()]
        assert p_ids2 == [p2_id]

        # 3. mem1 sees only Project 1
        client.cookies.set(settings.session_cookie_name, mem1_sess.id)
        resp_list_mem = client.get("/api/v1/projects")
        assert resp_list_mem.status_code == 200
        p_ids_mem = [p["id"] for p in resp_list_mem.json()]
        assert p_ids_mem == [p1_id]

        # 4. System Admin sees NO projects (no implicit business data access)
        client.cookies.set(settings.session_cookie_name, admin_sess.id)
        resp_list_admin = client.get("/api/v1/projects")
        assert resp_list_admin.status_code == 200
        assert resp_list_admin.json() == []

        # 5. Inaccessible read fails closed with 404 (does NOT disclose existence)
        # mem1 tries to read Project 2 (exists, but mem1 is not assigned)
        client.cookies.set(settings.session_cookie_name, mem1_sess.id)
        resp_read_unassigned = client.get(f"/api/v1/projects/{p2_id}")
        assert resp_read_unassigned.status_code == 404

        # Non-existent project also returns 404
        resp_read_nonexistent = client.get("/api/v1/projects/proj-does-not-exist")
        assert resp_read_nonexistent.status_code == 404

        # System Admin reading Project 1 returns 404
        client.cookies.set(settings.session_cookie_name, admin_sess.id)
        resp_read_admin = client.get(f"/api/v1/projects/{p1_id}")
        assert resp_read_admin.status_code == 404
    finally:
        engine.dispose()


def test_no_project_delete_route_ac06():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-del", "pmdel@example.com", Role.PROJECT_MANAGER
            )

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)
        resp = client.post(
            "/api/v1/projects",
            json={"name": "Project No Delete"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert resp.status_code == 201
        p_id = resp.json()["id"]

        # DELETE route must not exist (405 Method Not Allowed or 404 Not Found)
        del_resp = client.delete(
            f"/api/v1/projects/{p_id}",
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert del_resp.status_code in (404, 405)
    finally:
        engine.dispose()


def test_project_member_assignment_validation_and_audit_ac07():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-assign", "pmassign@example.com", Role.PROJECT_MANAGER
            )
            target_user, _ = create_user_and_session(
                db, settings, "user-target", "target@example.com", Role.MEMBER
            )
            inactive_user, _ = create_user_and_session(
                db, settings, "user-inact", "inact@example.com", Role.MEMBER, is_active=False
            )
            other_pm, other_pm_sess = create_user_and_session(
                db, settings, "pm-other", "other@example.com", Role.PROJECT_MANAGER
            )

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)

        # Create project
        resp = client.post(
            "/api/v1/projects",
            json={"name": "Project Assignment Test"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        p_id = resp.json()["id"]

        # 1. Successful member assignment with audit
        assign_resp = client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "user-target", "role": "member"},
            headers={"X-CSRF-Token": pm_sess.csrf_token, "X-Correlation-ID": "corr-assign-01"},
        )
        assert assign_resp.status_code == 201
        data = assign_resp.json()
        assert data["user_id"] == "user-target"
        assert data["role"] == "member"
        assert data["project_id"] == p_id

        # Verify audit record
        with SessionLocal() as db:
            audit = (
                db.query(AuditEvent)
                .filter_by(target_id=data["id"], action="project:member:assign")
                .first()
            )
            assert audit is not None
            assert audit.actor_id == "pm-assign"
            assert audit.project_id == p_id
            assert audit.after_values["role"] == "member"
            assert audit.after_values["user_id"] == "user-target"

        # 2. Reassignment (role update)
        reassign_resp = client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "user-target", "role": "auditor"},
            headers={"X-CSRF-Token": pm_sess.csrf_token, "X-Correlation-ID": "corr-assign-02"},
        )
        assert reassign_resp.status_code == 200
        assert reassign_resp.json()["role"] == "auditor"

        with SessionLocal() as db:
            audit_reassign = db.query(AuditEvent).filter_by(correlation_id="corr-assign-02").first()
            assert audit_reassign is not None
            assert audit_reassign.before_values["role"] == "member"
            assert audit_reassign.after_values["role"] == "auditor"

        # 3. Invalid role rejected
        invalid_role_resp = client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "user-target", "role": "super_admin"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert invalid_role_resp.status_code in (400, 422)

        # 4. Unknown target user rejected
        unknown_user_resp = client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "user-unknown", "role": "member"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert unknown_user_resp.status_code == 404

        # 5. Inactive target user rejected
        inactive_user_resp = client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "user-inact", "role": "member"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert inactive_user_resp.status_code == 400

        # 6. PM from another unassigned project cannot assign members (fails closed with 404)
        client.cookies.set(settings.session_cookie_name, other_pm_sess.id)
        other_assign_resp = client.post(
            f"/api/v1/projects/{p_id}/members",
            json={"user_id": "user-target", "role": "member"},
            headers={"X-CSRF-Token": other_pm_sess.csrf_token},
        )
        assert other_assign_resp.status_code == 404
    finally:
        engine.dispose()


def test_project_archive_lifecycle_and_audit():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-arc", "pmarc@example.com", Role.PROJECT_MANAGER
            )

        client = TestClient(app)
        client.cookies.set(settings.session_cookie_name, pm_sess.id)

        # Create project
        resp = client.post(
            "/api/v1/projects",
            json={"name": "Project Archive Test"},
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        p_id = resp.json()["id"]

        # Archive project
        archive_resp = client.post(
            f"/api/v1/projects/{p_id}/archive",
            headers={"X-CSRF-Token": pm_sess.csrf_token, "X-Correlation-ID": "corr-arch-01"},
        )
        assert archive_resp.status_code == 200
        assert archive_resp.json()["lifecycle"] == "archived"

        with SessionLocal() as db:
            proj = db.query(Project).filter_by(id=p_id).first()
            assert proj.lifecycle == "archived"

            audit = db.query(AuditEvent).filter_by(target_id=p_id, action="project:archive").first()
            assert audit is not None
            assert audit.before_values["lifecycle"] == "active"
            assert audit.after_values["lifecycle"] == "archived"
    finally:
        engine.dispose()


def test_department_match_without_explicit_project_membership_is_denied_ac10():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        synthetic_dept = "dept-synthetic-42"
        with SessionLocal() as db:
            pm, pm_sess = create_user_and_session(
                db, settings, "pm-dept", "pm-dept@example.com", Role.PROJECT_MANAGER
            )
            mem, mem_sess = create_user_and_session(
                db,
                settings,
                "mem-dept",
                "mem-dept@example.com",
                Role.MEMBER,
                department=synthetic_dept,
            )

        client = TestClient(app)

        # PM creates project with lead_department_id = synthetic_dept
        client.cookies.set(settings.session_cookie_name, pm_sess.id)
        proj_resp = client.post(
            "/api/v1/projects",
            json={
                "name": "Dept Matched Project",
                "description": "Project with matching department",
                "lead_department_id": synthetic_dept,
            },
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert proj_resp.status_code == 201
        project_id = proj_resp.json()["id"]

        # PM creates task in the project
        task_resp = client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Task in dept matched project",
                "description": "Synthetic task",
            },
            headers={"X-CSRF-Token": pm_sess.csrf_token},
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        # Fixture explicitly confirms department values match and caller has no membership row
        with SessionLocal() as db:
            proj = db.query(Project).filter_by(id=project_id).first()
            caller = db.query(User).filter_by(id="mem-dept").first()
            membership = (
                db.query(ProjectMember).filter_by(project_id=project_id, user_id="mem-dept").first()
            )
            assert proj is not None and caller is not None
            assert proj.lead_department_id == caller.department == synthetic_dept
            assert membership is None

        # Authenticate as the department-matched Member (without ProjectMember row)
        client.cookies.set(settings.session_cookie_name, mem_sess.id)

        # 1. GET /api/v1/projects returns no project IDs;
        #    GET /api/v1/dashboard/summary has no projects and zero totals
        resp_projects = client.get("/api/v1/projects")
        assert resp_projects.status_code == 200
        assert resp_projects.json() == []

        resp_dash = client.get("/api/v1/dashboard/summary")
        assert resp_dash.status_code == 200
        dash_data = resp_dash.json()
        assert dash_data["total_projects"] == 0
        assert dash_data["total_tasks"] == 0
        assert dash_data["projects"] == []

        # 2. GET /api/v1/projects/{project_id}, /members, /tasks, /api/v1/tasks/{task_id},
        #    and /api/v1/projects/{project_id}/audit-events return 404
        assert client.get(f"/api/v1/projects/{project_id}").status_code == 404
        assert client.get(f"/api/v1/projects/{project_id}/members").status_code == 404
        assert client.get(f"/api/v1/projects/{project_id}/tasks").status_code == 404
        assert client.get(f"/api/v1/tasks/{task_id}").status_code == 404
        assert client.get(f"/api/v1/projects/{project_id}/audit-events").status_code == 404

        # 3. With valid CSRF, PATCH /api/v1/tasks/{task_id}/status
        #    and POST /api/v1/projects/{project_id}/archive return 404
        patch_resp = client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "in_progress"},
            headers={"X-CSRF-Token": mem_sess.csrf_token},
        )
        assert patch_resp.status_code == 404

        archive_resp = client.post(
            f"/api/v1/projects/{project_id}/archive",
            headers={"X-CSRF-Token": mem_sess.csrf_token},
        )
        assert archive_resp.status_code == 404

        # 4. Task remains 'open'; project remains 'active';
        #    no task:transition or project:archive audit event is written
        with SessionLocal() as db:
            task = db.query(Task).filter_by(id=task_id).first()
            assert task is not None
            assert task.status == "open"

            proj = db.query(Project).filter_by(id=project_id).first()
            assert proj is not None
            assert proj.lifecycle == "active"

            assert db.query(AuditEvent).filter_by(action="task:transition").first() is None
            assert db.query(AuditEvent).filter_by(action="project:archive").first() is None
    finally:
        engine.dispose()


def test_http_authorization_matrix_projects_ac17():
    app, SessionLocal, settings, engine = setup_test_env()
    try:
        with SessionLocal() as db:
            pm1, s_pm1 = create_user_with_roles_and_session(
                db, settings, "u-pm1", "pm1@corp.local", [Role.PROJECT_MANAGER]
            )
            pm2, s_pm2 = create_user_with_roles_and_session(
                db, settings, "u-pm2", "pm2@corp.local", [Role.PROJECT_MANAGER]
            )
            mem1, s_mem1 = create_user_with_roles_and_session(
                db, settings, "u-mem1", "mem1@corp.local", [Role.MEMBER]
            )
            aud1, s_aud1 = create_user_with_roles_and_session(
                db, settings, "u-aud1", "aud1@corp.local", [Role.AUDITOR]
            )
            admin1, s_admin1 = create_user_with_roles_and_session(
                db, settings, "u-admin1", "admin1@corp.local", [Role.SYSTEM_ADMIN]
            )
            sa_pm, s_sa_pm = create_user_with_roles_and_session(
                db, settings, "u-sapm", "sapm@corp.local", [Role.SYSTEM_ADMIN, Role.PROJECT_MANAGER]
            )
            pm_mem, s_pm_mem = create_user_with_roles_and_session(
                db, settings, "u-pmmem", "pmmem@corp.local", [Role.PROJECT_MANAGER, Role.MEMBER]
            )
            pm_aud, s_pm_aud = create_user_with_roles_and_session(
                db, settings, "u-pmaud", "pmaud@corp.local", [Role.PROJECT_MANAGER, Role.AUDITOR]
            )
            mem_aud, s_mem_aud = create_user_with_roles_and_session(
                db, settings, "u-memaud", "memaud@corp.local", [Role.MEMBER, Role.AUDITOR]
            )
            unassigned, s_unassigned = create_user_with_roles_and_session(
                db, settings, "u-unassigned", "unassigned@corp.local", [Role.PROJECT_MANAGER]
            )
            dept_only, s_dept_only = create_user_with_roles_and_session(
                db, settings, "u-dept", "dept@corp.local", [Role.MEMBER], department="dept-p1"
            )

            # Target user to assign
            target_u, _ = create_user_with_roles_and_session(
                db, settings, "u-target", "target@corp.local", [Role.MEMBER]
            )

        client = TestClient(app)

        # 1. POST /api/v1/projects
        # PM succeeds (201)
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        r_create_pm1 = client.post(
            "/api/v1/projects",
            json={"name": "Project P1", "lead_department_id": "dept-p1"},
            headers={"X-CSRF-Token": s_pm1.csrf_token},
        )
        assert r_create_pm1.status_code == 201
        p1_id = r_create_pm1.json()["id"]

        # PM2 creates P2
        client.cookies.set(settings.session_cookie_name, s_pm2.id)
        r_create_pm2 = client.post(
            "/api/v1/projects",
            json={"name": "Project P2", "lead_department_id": "dept-p2"},
            headers={"X-CSRF-Token": s_pm2.csrf_token},
        )
        assert r_create_pm2.status_code == 201
        p2_id = r_create_pm2.json()["id"]

        # Non-PM and Multi-role users cannot create project -> 403
        for s_user in (s_mem1, s_aud1, s_admin1, s_sa_pm, s_pm_mem, s_pm_aud, s_mem_aud):
            client.cookies.set(settings.session_cookie_name, s_user.id)
            r_deny = client.post(
                "/api/v1/projects",
                json={"name": "Forbidden Project"},
                headers={"X-CSRF-Token": s_user.csrf_token},
            )
            assert r_deny.status_code == 403

        # Seed memberships on P1:
        # mem1 -> member; aud1 -> auditor; admin1 -> synthetic project_manager;
        # sa_pm -> project_manager; pm_mem -> member; pm_aud -> auditor; mem_aud -> member
        with SessionLocal() as db:
            from app.projects.models import utc_now

            now = utc_now()
            db.add_all(
                [
                    ProjectMember(
                        id="pm-mem1",
                        project_id=p1_id,
                        user_id=mem1.id,
                        role="member",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-aud1",
                        project_id=p1_id,
                        user_id=aud1.id,
                        role="auditor",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-admin1",
                        project_id=p1_id,
                        user_id=admin1.id,
                        role="project_manager",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-sapm",
                        project_id=p1_id,
                        user_id=sa_pm.id,
                        role="project_manager",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-pmmem",
                        project_id=p1_id,
                        user_id=pm_mem.id,
                        role="member",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-pmaud",
                        project_id=p1_id,
                        user_id=pm_aud.id,
                        role="auditor",
                        assigned_by=pm1.id,
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectMember(
                        id="pm-memaud",
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

        # 2. GET /api/v1/projects
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        assert [p["id"] for p in client.get("/api/v1/projects").json()] == [p1_id]

        client.cookies.set(settings.session_cookie_name, s_mem1.id)
        assert [p["id"] for p in client.get("/api/v1/projects").json()] == [p1_id]

        client.cookies.set(settings.session_cookie_name, s_pm_mem.id)
        assert [p["id"] for p in client.get("/api/v1/projects").json()] == [p1_id]

        # Auditor, System Admin, Multi-role (sa_pm, pm_aud, mem_aud), unassigned, dept_only -> []
        for s_user in (s_aud1, s_admin1, s_sa_pm, s_pm_aud, s_mem_aud, s_unassigned, s_dept_only):
            client.cookies.set(settings.session_cookie_name, s_user.id)
            assert client.get("/api/v1/projects").json() == []

        # 3. GET /api/v1/projects/{project_id}
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        assert client.get(f"/api/v1/projects/{p1_id}").status_code == 200
        assert client.get(f"/api/v1/projects/{p2_id}").status_code == 404

        client.cookies.set(settings.session_cookie_name, s_mem1.id)
        assert client.get(f"/api/v1/projects/{p1_id}").status_code == 200
        assert client.get(f"/api/v1/projects/{p2_id}").status_code == 404

        client.cookies.set(settings.session_cookie_name, s_pm_mem.id)
        assert client.get(f"/api/v1/projects/{p1_id}").status_code == 200

        for s_user in (s_aud1, s_admin1, s_sa_pm, s_pm_aud, s_mem_aud, s_unassigned, s_dept_only):
            client.cookies.set(settings.session_cookie_name, s_user.id)
            assert client.get(f"/api/v1/projects/{p1_id}").status_code == 404

        # 4. POST /api/v1/projects/{project_id}/members and /assignments
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        r_assign_pm1 = client.post(
            f"/api/v1/projects/{p1_id}/members",
            json={"user_id": target_u.id, "role": "member"},
            headers={"X-CSRF-Token": s_pm1.csrf_token},
        )
        assert r_assign_pm1.status_code == 201

        # Unassigned / cross-project PM -> 404
        client.cookies.set(settings.session_cookie_name, s_pm2.id)
        r_pm2_assign = client.post(
            f"/api/v1/projects/{p1_id}/members",
            json={"user_id": target_u.id, "role": "member"},
            headers={"X-CSRF-Token": s_pm2.csrf_token},
        )
        assert r_pm2_assign.status_code == 404

        client.cookies.set(settings.session_cookie_name, s_unassigned.id)
        r_unassigned_assign = client.post(
            f"/api/v1/projects/{p1_id}/members",
            json={"user_id": target_u.id, "role": "member"},
            headers={"X-CSRF-Token": s_unassigned.csrf_token},
        )
        assert r_unassigned_assign.status_code == 404

        # In-scope non-PM or multi-role users cannot assign members -> 403
        for s_user in (s_mem1, s_aud1, s_admin1, s_sa_pm, s_pm_mem, s_pm_aud, s_mem_aud):
            client.cookies.set(settings.session_cookie_name, s_user.id)
            r_assign_deny = client.post(
                f"/api/v1/projects/{p1_id}/members",
                json={"user_id": target_u.id, "role": "member"},
                headers={"X-CSRF-Token": s_user.csrf_token},
            )
            assert r_assign_deny.status_code == 403

        # 5. GET /api/v1/projects/{project_id}/members
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        assert client.get(f"/api/v1/projects/{p1_id}/members").status_code == 200

        client.cookies.set(settings.session_cookie_name, s_mem1.id)
        assert client.get(f"/api/v1/projects/{p1_id}/members").status_code == 200

        client.cookies.set(settings.session_cookie_name, s_pm_mem.id)
        assert client.get(f"/api/v1/projects/{p1_id}/members").status_code == 200

        for s_user in (s_aud1, s_admin1, s_sa_pm, s_pm_aud, s_mem_aud, s_unassigned, s_dept_only):
            client.cookies.set(settings.session_cookie_name, s_user.id)
            assert client.get(f"/api/v1/projects/{p1_id}/members").status_code == 404

        # 6. POST /api/v1/projects/{project_id}/archive
        # Unassigned / cross-project PM -> 404
        client.cookies.set(settings.session_cookie_name, s_pm2.id)
        assert (
            client.post(
                f"/api/v1/projects/{p1_id}/archive",
                headers={"X-CSRF-Token": s_pm2.csrf_token},
            ).status_code
            == 404
        )

        # In-scope non-PM or multi-role users cannot archive -> 403
        for s_user in (s_mem1, s_aud1, s_admin1, s_sa_pm, s_pm_mem, s_pm_aud, s_mem_aud):
            client.cookies.set(settings.session_cookie_name, s_user.id)
            assert (
                client.post(
                    f"/api/v1/projects/{p1_id}/archive",
                    headers={"X-CSRF-Token": s_user.csrf_token},
                ).status_code
                == 403
            )

        # PM in scope archives -> 200
        client.cookies.set(settings.session_cookie_name, s_pm1.id)
        assert (
            client.post(
                f"/api/v1/projects/{p1_id}/archive",
                headers={"X-CSRF-Token": s_pm1.csrf_token},
            ).status_code
            == 200
        )
    finally:
        engine.dispose()
