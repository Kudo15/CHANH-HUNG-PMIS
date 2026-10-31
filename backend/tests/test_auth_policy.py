import pytest

from app.auth.policy import (
    Action,
    AuthorizationError,
    Principal,
    ProjectScopeResolver,
    ResourceContext,
    Role,
    authorize,
    grant_system_admin,
    revoke_system_admin,
)


class MockProjectScopeResolver(ProjectScopeResolver):
    def __init__(self):
        # task_id -> project_id
        self.task_projects: dict[str, str] = {}
        # (user_id, project_id) -> bool
        self.project_assignments: set[tuple[str, str]] = set()
        # (user_id, task_id) -> bool
        self.task_assignments: set[tuple[str, str]] = set()

    def get_project_for_task(self, task_id: str) -> str | None:
        return self.task_projects.get(task_id)

    def is_user_assigned_to_project(
        self, user_id: str, project_id: str, required_role: str | None = None
    ) -> bool:
        return (user_id, project_id) in self.project_assignments

    def is_user_assigned_to_task(self, user_id: str, task_id: str) -> bool:
        return (user_id, task_id) in self.task_assignments


def test_deny_by_default():
    user = Principal(
        id="u1", sub="s1", email="u1@test.com", name="User 1", roles=[], department="IT"
    )
    # No roles -> deny any action
    assert authorize(user, Action.PROJECT_READ, ResourceContext(project_id="p1")) is False
    assert authorize(user, Action.TASK_READ, ResourceContext(task_id="t1")) is False
    assert authorize(user, Action.ROLE_GRANT) is False
    assert authorize(user, "unknown:action") is False


def test_system_admin_no_implicit_business_data_access():
    admin = Principal(
        id="admin1", sub="s_admin", email="admin@test.com", name="Admin", roles=[Role.SYSTEM_ADMIN]
    )
    resolver = MockProjectScopeResolver()

    # System admin CAN manage roles/users
    assert authorize(admin, Action.ROLE_GRANT) is True
    assert authorize(admin, Action.ROLE_REVOKE) is True
    assert authorize(admin, Action.USER_DEPROVISION) is True

    # System admin is DENIED implicit business data access
    assert (
        authorize(admin, Action.PROJECT_READ, ResourceContext(project_id="p1"), resolver) is False
    )
    assert authorize(admin, Action.PROJECT_CREATE, None, resolver) is False
    assert (
        authorize(admin, Action.PROJECT_MANAGE, ResourceContext(project_id="p1"), resolver) is False
    )
    assert authorize(admin, Action.TASK_READ, ResourceContext(task_id="t1"), resolver) is False
    assert authorize(admin, Action.TASK_UPDATE, ResourceContext(task_id="t1"), resolver) is False
    assert authorize(admin, Action.AUDIT_READ, ResourceContext(project_id="p1"), resolver) is False


def test_system_admin_self_grant_denied():
    admin1 = Principal(
        id="admin1", sub="s1", email="a1@test.com", name="Admin 1", roles=[Role.SYSTEM_ADMIN]
    )
    admin2 = Principal(
        id="admin2", sub="s2", email="a2@test.com", name="Admin 2", roles=[Role.SYSTEM_ADMIN]
    )

    # Admin cannot self-grant system_admin
    with pytest.raises(AuthorizationError, match="cannot self-grant"):
        grant_system_admin(
            actor=admin1,
            target_user_id="admin1",
            second_admin=admin2,
            existing_admin_ids={"admin1", "admin2"},
        )


def test_system_admin_grant_requires_second_admin():
    admin1 = Principal(
        id="admin1", sub="s1", email="a1@test.com", name="Admin 1", roles=[Role.SYSTEM_ADMIN]
    )
    non_admin = Principal(
        id="user2", sub="s2", email="u2@test.com", name="User 2", roles=[Role.MEMBER]
    )

    # Missing second admin
    with pytest.raises(AuthorizationError, match="distinct second existing System Admin"):
        grant_system_admin(
            actor=admin1,
            target_user_id="u_target",
            second_admin=None,
            existing_admin_ids={"admin1"},
        )

    # Second admin is the same as actor
    with pytest.raises(AuthorizationError, match="distinct second existing System Admin"):
        grant_system_admin(
            actor=admin1,
            target_user_id="u_target",
            second_admin=admin1,
            existing_admin_ids={"admin1"},
        )

    # Second admin is target
    target_admin = Principal(id="u_target", sub="st", email="t@test.com", name="Target", roles=[])
    with pytest.raises(AuthorizationError, match="distinct second existing System Admin"):
        grant_system_admin(
            actor=admin1,
            target_user_id="u_target",
            second_admin=target_admin,
            existing_admin_ids={"admin1"},
        )

    # Second admin is not an existing system admin
    with pytest.raises(AuthorizationError, match="active existing System Admin"):
        grant_system_admin(
            actor=admin1,
            target_user_id="u_target",
            second_admin=non_admin,
            existing_admin_ids={"admin1"},
        )


def test_system_admin_grant_and_revocation_with_second_admin_succeeds():
    admin1 = Principal(
        id="admin1", sub="s1", email="a1@test.com", name="Admin 1", roles=[Role.SYSTEM_ADMIN]
    )
    admin2 = Principal(
        id="admin2", sub="s2", email="a2@test.com", name="Admin 2", roles=[Role.SYSTEM_ADMIN]
    )

    # Valid grant
    result = grant_system_admin(
        actor=admin1,
        target_user_id="target_user",
        second_admin=admin2,
        existing_admin_ids={"admin1", "admin2"},
    )
    assert result is True

    # Valid revoke
    revoke_res = revoke_system_admin(
        actor=admin1,
        target_user_id="target_user",
        second_admin=admin2,
        existing_admin_ids={"admin1", "admin2", "target_user"},
    )
    assert revoke_res is True

    # Cannot self-revoke if second admin is missing or self
    with pytest.raises(AuthorizationError, match="distinct second existing System Admin"):
        revoke_system_admin(
            actor=admin1,
            target_user_id="admin1",
            second_admin=admin1,
            existing_admin_ids={"admin1", "admin2"},
        )


def test_department_membership_alone_grants_no_project_access():
    user = Principal(
        id="u_dept",
        sub="sd",
        email="d@test.com",
        name="Dept User",
        roles=[Role.PROJECT_MANAGER],
        department="Civil",
    )
    resolver = MockProjectScopeResolver()
    # User is in Civil department, project has department Civil, but user is NOT assigned to project
    ctx = ResourceContext(project_id="p_civil", department="Civil")
    assert authorize(user, Action.PROJECT_READ, ctx, resolver) is False
    assert authorize(user, Action.PROJECT_MANAGE, ctx, resolver) is False


def test_project_manager_scoped_to_assigned_project():
    pm = Principal(
        id="pm1", sub="spm", email="pm@test.com", name="PM 1", roles=[Role.PROJECT_MANAGER]
    )
    resolver = MockProjectScopeResolver()
    resolver.project_assignments.add(("pm1", "proj_assigned"))

    # PM can create projects (subject to system rules)
    assert authorize(pm, Action.PROJECT_CREATE, None, resolver) is True

    # In assigned project: allowed
    ctx_assigned = ResourceContext(project_id="proj_assigned")
    assert authorize(pm, Action.PROJECT_READ, ctx_assigned, resolver) is True
    assert authorize(pm, Action.PROJECT_MANAGE, ctx_assigned, resolver) is True
    assert authorize(pm, Action.PROJECT_ASSIGN, ctx_assigned, resolver) is True
    assert authorize(pm, Action.TASK_CREATE, ctx_assigned, resolver) is True
    assert authorize(pm, Action.AUDIT_READ, ctx_assigned, resolver) is True

    # In unassigned project: DENIED
    ctx_unassigned = ResourceContext(project_id="proj_other")
    assert authorize(pm, Action.PROJECT_READ, ctx_unassigned, resolver) is False
    assert authorize(pm, Action.PROJECT_MANAGE, ctx_unassigned, resolver) is False
    assert authorize(pm, Action.TASK_CREATE, ctx_unassigned, resolver) is False
    assert authorize(pm, Action.AUDIT_READ, ctx_unassigned, resolver) is False


def test_member_permissions_and_own_task_update():
    member = Principal(
        id="m1", sub="sm1", email="m1@test.com", name="Member 1", roles=[Role.MEMBER]
    )
    resolver = MockProjectScopeResolver()
    resolver.project_assignments.add(("m1", "proj_1"))
    resolver.task_projects["task_own"] = "proj_1"
    resolver.task_projects["task_other_member"] = "proj_1"
    resolver.task_projects["task_other_proj"] = "proj_2"

    resolver.task_assignments.add(("m1", "task_own"))
    resolver.task_assignments.add(("m2", "task_other_member"))

    # Can read assigned project
    assert (
        authorize(member, Action.PROJECT_READ, ResourceContext(project_id="proj_1"), resolver)
        is True
    )
    # Cannot manage assigned project
    assert (
        authorize(member, Action.PROJECT_MANAGE, ResourceContext(project_id="proj_1"), resolver)
        is False
    )
    # Cannot create task
    assert (
        authorize(member, Action.TASK_CREATE, ResourceContext(project_id="proj_1"), resolver)
        is False
    )
    # Cannot read unassigned project
    assert (
        authorize(member, Action.PROJECT_READ, ResourceContext(project_id="proj_2"), resolver)
        is False
    )

    # Can read task in assigned project
    assert (
        authorize(member, Action.TASK_READ, ResourceContext(task_id="task_own"), resolver) is True
    )
    assert (
        authorize(member, Action.TASK_READ, ResourceContext(task_id="task_other_member"), resolver)
        is True
    )
    # Cannot read task in unassigned project
    assert (
        authorize(member, Action.TASK_READ, ResourceContext(task_id="task_other_proj"), resolver)
        is False
    )

    # Can update ONLY own assigned task
    assert (
        authorize(member, Action.TASK_UPDATE, ResourceContext(task_id="task_own"), resolver) is True
    )
    # Cannot update other member's task even in same project
    assert (
        authorize(
            member, Action.TASK_UPDATE, ResourceContext(task_id="task_other_member"), resolver
        )
        is False
    )

    # Cannot read audit
    assert (
        authorize(member, Action.AUDIT_READ, ResourceContext(project_id="proj_1"), resolver)
        is False
    )


def test_auditor_permissions():
    auditor = Principal(
        id="aud1", sub="saud", email="aud@test.com", name="Auditor 1", roles=[Role.AUDITOR]
    )
    resolver = MockProjectScopeResolver()
    resolver.project_assignments.add(("aud1", "proj_1"))

    # Can read audit in assigned project
    assert (
        authorize(auditor, Action.AUDIT_READ, ResourceContext(project_id="proj_1"), resolver)
        is True
    )
    # Cannot read audit in unassigned project
    assert (
        authorize(auditor, Action.AUDIT_READ, ResourceContext(project_id="proj_2"), resolver)
        is False
    )
    # Cannot mutate business data in assigned project
    assert (
        authorize(auditor, Action.PROJECT_MANAGE, ResourceContext(project_id="proj_1"), resolver)
        is False
    )
    assert (
        authorize(auditor, Action.TASK_CREATE, ResourceContext(project_id="proj_1"), resolver)
        is False
    )
    assert authorize(auditor, Action.TASK_UPDATE, ResourceContext(task_id="t1"), resolver) is False


def test_system_admin_api_endpoints():
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.auth.models import Session, User, UserRole
    from app.auth.session import create_session
    from app.config import Settings
    from app.database import Base
    from app.main import create_app

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    settings = Settings(database_url=None)
    app = create_app(settings)
    app.state.engine = engine

    try:
        with TestingSessionLocal() as db:
            admin1 = User(
                id="admin1", sub="s_a1", email="a1@test.com", name="Admin 1", is_active=True
            )
            admin2 = User(
                id="admin2", sub="s_a2", email="a2@test.com", name="Admin 2", is_active=True
            )
            user1 = User(id="user1", sub="s_u1", email="u1@test.com", name="User 1", is_active=True)
            db.add_all([admin1, admin2, user1])
            db.commit()

            db.add(UserRole(id="r1", user_id="admin1", role=Role.SYSTEM_ADMIN, granted_by="seed"))
            db.add(UserRole(id="r2", user_id="admin2", role=Role.SYSTEM_ADMIN, granted_by="seed"))
            db.commit()

            admin_sess = create_session(db, admin1.id, settings)
            admin_sess_id = admin_sess.id
            admin_csrf = admin_sess.csrf_token

            admin2_sess = create_session(db, admin2.id, settings)
            admin2_sess_id = admin2_sess.id
            admin2_csrf = admin2_sess.csrf_token

            user_sess = create_session(db, user1.id, settings)
            user_sess_id = user_sess.id
            user_csrf = user_sess.csrf_token

        client = TestClient(app)

        # 1. Unauthenticated -> 401
        resp = client.post(
            "/api/v1/auth/roles/system-admin/grant",
            json={"target_user_id": "user1"},
        )
        assert resp.status_code == 401

        # 2. Non-admin caller -> 403
        client.cookies.set("pmis_session", user_sess_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/grant",
            json={"target_user_id": "user1"},
            headers={"X-CSRF-Token": user_csrf},
        )
        assert resp.status_code == 403

        # 3. Admin self-grant -> 403
        client.cookies.set("pmis_session", admin_sess_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/grant",
            json={"target_user_id": "admin1"},
            headers={"X-CSRF-Token": admin_csrf},
        )
        assert resp.status_code == 403

        # 4. Valid grant request by Admin 1 -> 202 (pending approval)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/grant",
            json={"target_user_id": "user1"},
            headers={"X-CSRF-Token": admin_csrf},
        )
        assert resp.status_code in (200, 202)
        grant_req_id = resp.json()["request_id"]
        assert resp.json()["status"] == "pending_approval"

        # Verify role is not yet granted
        with TestingSessionLocal() as db:
            grant = db.query(UserRole).filter_by(user_id="user1", role=Role.SYSTEM_ADMIN).first()
            assert grant is None

        # 5. Requester (Admin 1) cannot approve own request
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": grant_req_id},
            headers={"X-CSRF-Token": admin_csrf},
        )
        assert resp.status_code == 403

        # 6. Admin 2 (second authenticated System Admin) approves the request
        client.cookies.set("pmis_session", admin2_sess_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": grant_req_id},
            headers={"X-CSRF-Token": admin2_csrf},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

        # Verify UserRole persisted and target sessions revoked
        with TestingSessionLocal() as db:
            grant = db.query(UserRole).filter_by(user_id="user1", role=Role.SYSTEM_ADMIN).first()
            assert grant is not None
            assert grant.granted_by == "admin1"
            assert grant.second_admin_id == "admin2"

            # user1's prior session should be revoked
            prior_sess = db.query(Session).filter_by(id=user_sess_id).first()
            assert prior_sess.is_revoked is True

        # 7. Replay attack: approving again fails closed
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": grant_req_id},
            headers={"X-CSRF-Token": admin2_csrf},
        )
        assert resp.status_code in (400, 409)

        # 8. Revoke system_admin: Admin 1 requests revocation
        client.cookies.set("pmis_session", admin_sess_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/revoke",
            json={"target_user_id": "user1"},
            headers={"X-CSRF-Token": admin_csrf},
        )
        assert resp.status_code in (200, 202)
        revoke_req_id = resp.json()["request_id"]
        assert resp.json()["status"] == "pending_approval"

        # Admin 2 approves revocation
        client.cookies.set("pmis_session", admin2_sess_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": revoke_req_id},
            headers={"X-CSRF-Token": admin2_csrf},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

        with TestingSessionLocal() as db:
            grant = db.query(UserRole).filter_by(user_id="user1", role=Role.SYSTEM_ADMIN).first()
            assert grant is None
    finally:
        engine.dispose()
