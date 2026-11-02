import base64
import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.bootstrap_admins import (
    REG_BINARY,
    REGISTRY_NAMESPACE_PATH,
    REGISTRY_ROOT_PATH,
    REGISTRY_TRUST_KEY_PATH,
    VAL_PROJECT_OWNER,
    VAL_SECURITY_REVIEWER,
    BootstrapError,
    SyntheticRegistryBackend,
    bootstrap_initial_admins,
    create_canonical_payload,
    get_or_create_instance_state,
)
from app.auth.models import OIDCState, Session, SystemAdminRequest, User, UserRole
from app.auth.oidc import (
    StaticKeyResolver,
    decode_and_verify_id_token,
    initiate_login,
)
from app.auth.policy import Role
from app.auth.session import create_session, validate_session
from app.config import Settings
from app.database import Base
from app.main import create_app


def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_key, public_pem


def make_signed_token(
    payload: dict,
    private_key,
    kid: str = "test-key-1",
    algorithm: str = "RS256",
    headers: dict | None = None,
) -> str:
    h = {"kid": kid, "typ": "JWT", "alg": algorithm}
    if headers:
        h.update(headers)
    return jwt.encode(payload, private_key, algorithm=algorithm, headers=h)


def get_test_setup():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    settings = Settings(
        database_url=None,
        oidc_issuer="https://idp.example.com",
        oidc_client_id="pmis-app",
        oidc_authorization_endpoint="https://idp.example.com/oauth/authorize",
        oidc_token_endpoint="https://idp.example.com/oauth/token",
        oidc_redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
        session_cookie_secure=True,
    )
    app = create_app(settings)
    app.state.engine = engine
    return app, TestingSessionLocal, settings, engine


def test_signature_verification_and_forgery_fail_closed():
    priv_key, pub_pem = generate_rsa_key_pair()
    resolver = StaticKeyResolver({"key-1": pub_pem})

    valid_payload = {
        "iss": "https://idp.example.com",
        "aud": "pmis-app",
        "sub": "user-123",
        "nonce": "correct-nonce",
        "exp": int(time.time()) + 3600,
        "email": "user@example.com",
        "name": "User One",
    }
    valid_token = make_signed_token(valid_payload, priv_key, kid="key-1")

    # 1. Valid token succeeds
    claims = decode_and_verify_id_token(
        id_token=valid_token,
        expected_issuer="https://idp.example.com",
        expected_audience="pmis-app",
        expected_nonce="correct-nonce",
        key_resolver=resolver,
        allowed_algorithms=["RS256"],
    )
    assert claims["sub"] == "user-123"

    # 2. Forged signature fails closed
    parts = valid_token.split(".")
    tampered_sig_token = f"{parts[0]}.{parts[1]}.dGFtcGVyZWRfc2lnbmF0dXJl"
    with pytest.raises(Exception) as exc_info:
        decode_and_verify_id_token(
            id_token=tampered_sig_token,
            expected_issuer="https://idp.example.com",
            expected_audience="pmis-app",
            expected_nonce="correct-nonce",
            key_resolver=resolver,
        )
    assert getattr(exc_info.value, "status_code", 400) == 400

    # 3. Unknown kid fails closed
    unknown_kid_token = make_signed_token(valid_payload, priv_key, kid="unknown-kid")
    with pytest.raises(Exception) as exc_info:
        decode_and_verify_id_token(
            id_token=unknown_kid_token,
            expected_issuer="https://idp.example.com",
            expected_audience="pmis-app",
            expected_nonce="correct-nonce",
            key_resolver=resolver,
        )
    assert getattr(exc_info.value, "status_code", 400) == 400

    # 4. Unsupported algorithm fails closed
    hs256_token = jwt.encode(
        valid_payload,
        "symmetric-secret-key-at-least-32-bytes-long!",
        algorithm="HS256",
    )
    with pytest.raises(Exception) as exc_info:
        decode_and_verify_id_token(
            id_token=hs256_token,
            expected_issuer="https://idp.example.com",
            expected_audience="pmis-app",
            expected_nonce="correct-nonce",
            key_resolver=resolver,
            allowed_algorithms=["RS256"],
        )
    assert getattr(exc_info.value, "status_code", 400) == 400


def test_login_redirect_uri_is_fixed_and_rejects_manipulation():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            # Calling initiate_login should strictly use settings.oidc_redirect_uri
            auth_url = initiate_login(db, settings)
            expected_cb = "redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Fv1%2Fauth%2Fcallback"
            assert expected_cb in auth_url

            state = db.query(OIDCState).first()
            assert state is not None
            assert state.redirect_uri == settings.oidc_redirect_uri

        client = TestClient(app)
        # Attempt redirect manipulation via query parameter
        resp = client.get(
            "/api/v1/auth/login?redirect_uri=https://evil.example.com/steal-code",
            follow_redirects=False,
        )
        assert resp.status_code in (302, 303, 307)
        loc = resp.headers["location"]
        assert "evil.example.com" not in loc
        assert "redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Fv1%2Fauth%2Fcallback" in loc
    finally:
        engine.dispose()


def test_login_prunes_expired_oidc_states_bounded():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        now = time.time()
        with SessionLocal() as db:
            # Seed 1 expired state and 1 unexpired state
            expired = OIDCState(
                state="stale-state",
                nonce="stale-nonce",
                redirect_uri=settings.oidc_redirect_uri,
                created_at=now - 1200,
                expires_at=now - 600,
            )
            valid = OIDCState(
                state="active-state",
                nonce="active-nonce",
                redirect_uri=settings.oidc_redirect_uri,
                created_at=now - 60,
                expires_at=now + 540,
            )
            db.add_all([expired, valid])
            db.commit()

            # Now initiate login
            initiate_login(db, settings)

            # Expired must be gone; valid must remain
            remaining_states = {s.state for s in db.query(OIDCState).all()}
            assert "stale-state" not in remaining_states
            assert "active-state" in remaining_states
    finally:
        engine.dispose()


def test_system_admin_two_step_request_and_approval_flow():
    app, TestingSessionLocal, settings, engine = get_test_setup()
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

            sess1 = create_session(db, admin1.id, settings)
            admin1_sess_id = sess1.id
            admin1_csrf = sess1.csrf_token

            sess2 = create_session(db, admin2.id, settings)
            admin2_sess_id = sess2.id
            admin2_csrf = sess2.csrf_token

            sess_u = create_session(db, user1.id, settings)
            user_sess_id = sess_u.id
            user_csrf = sess_u.csrf_token

        client = TestClient(app)

        # 1. Non-admin cannot request grant
        client.cookies.set("pmis_session", user_sess_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/grant",
            json={"target_user_id": "user1"},
            headers={"X-CSRF-Token": user_csrf},
        )
        assert resp.status_code == 403

        # 2. Admin 1 requests grant of System Admin to User 1
        client.cookies.set("pmis_session", admin1_sess_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/grant",
            json={"target_user_id": "user1"},
            headers={"X-CSRF-Token": admin1_csrf},
        )
        assert resp.status_code in (200, 202)
        grant_req_data = resp.json()
        assert grant_req_data["status"] == "pending_approval"
        request_id = grant_req_data["request_id"]

        # Verify role is NOT yet granted to User 1
        with TestingSessionLocal() as db:
            grant = db.query(UserRole).filter_by(user_id="user1", role=Role.SYSTEM_ADMIN).first()
            assert grant is None
            req_row = db.query(SystemAdminRequest).filter_by(id=request_id).first()
            assert req_row is not None
            assert req_row.status == "pending"
            assert req_row.requester_id == "admin1"

        # 3. Requester cannot approve own request (dual-control enforcement)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": request_id},
            headers={"X-CSRF-Token": admin1_csrf},
        )
        assert resp.status_code == 403

        # 4. Admin cannot self-grant
        resp = client.post(
            "/api/v1/auth/roles/system-admin/grant",
            json={"target_user_id": "admin1"},
            headers={"X-CSRF-Token": admin1_csrf},
        )
        assert resp.status_code == 403

        # 5. Admin 2 (second authenticated System Admin) approves the request
        client.cookies.set("pmis_session", admin2_sess_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": request_id},
            headers={"X-CSRF-Token": admin2_csrf},
        )
        assert resp.status_code == 200
        approve_data = resp.json()
        assert approve_data["status"] in ("approved", "granted")

        # Verify role IS granted, target's session was revoked, and request record is durable
        with TestingSessionLocal() as db:
            grant = db.query(UserRole).filter_by(user_id="user1", role=Role.SYSTEM_ADMIN).first()
            assert grant is not None
            assert grant.granted_by == "admin1"
            assert grant.second_admin_id == "admin2"

            u_sess = db.query(Session).filter_by(id=user_sess_id).first()
            assert u_sess.is_revoked is True

            req_row = db.query(SystemAdminRequest).filter_by(id=request_id).first()
            assert req_row.status == "approved"
            assert req_row.approver_id == "admin2"
            assert req_row.decided_at is not None

        # 6. Replay attack: approving the already-approved request fails closed
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": request_id},
            headers={"X-CSRF-Token": admin2_csrf},
        )
        assert resp.status_code in (400, 409)

        # 7. Revocation two-step flow: Admin 1 requests revocation of User 1
        client.cookies.set("pmis_session", admin1_sess_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/revoke",
            json={"target_user_id": "user1"},
            headers={"X-CSRF-Token": admin1_csrf},
        )
        assert resp.status_code in (200, 202)
        revoke_req_data = resp.json()
        assert revoke_req_data["status"] == "pending_approval"
        revoke_req_id = revoke_req_data["request_id"]

        # Verify role still present before approval
        with TestingSessionLocal() as db:
            grant = db.query(UserRole).filter_by(user_id="user1", role=Role.SYSTEM_ADMIN).first()
            assert grant is not None

        # Admin 2 approves revocation
        client.cookies.set("pmis_session", admin2_sess_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": revoke_req_id},
            headers={"X-CSRF-Token": admin2_csrf},
        )
        assert resp.status_code == 200

        # Verify role revoked and history durable
        with TestingSessionLocal() as db:
            grant = db.query(UserRole).filter_by(user_id="user1", role=Role.SYSTEM_ADMIN).first()
            assert grant is None
            rev_row = db.query(SystemAdminRequest).filter_by(id=revoke_req_id).first()
            assert rev_row.status == "approved"
            assert rev_row.approver_id == "admin2"
    finally:
        engine.dispose()


def generate_ed25519_keypair():
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv, pub_bytes


def make_valid_synthetic_registry(po_bytes: bytes, sr_bytes: bytes) -> SyntheticRegistryBackend:
    keys = {
        REGISTRY_ROOT_PATH: {
            "dacl_present": True,
            "dacl_protected": False,
            "prohibited_rights_granted": False,
        },
        REGISTRY_NAMESPACE_PATH: {
            "dacl_present": True,
            "dacl_protected": True,
            "prohibited_rights_granted": False,
        },
        REGISTRY_TRUST_KEY_PATH: {
            "dacl_present": True,
            "dacl_protected": True,
            "prohibited_rights_granted": False,
            "values": {
                VAL_PROJECT_OWNER: (REG_BINARY, po_bytes),
                VAL_SECURITY_REVIEWER: (REG_BINARY, sr_bytes),
            },
        },
    }
    return SyntheticRegistryBackend(is_windows=True, keys=keys)


def sign_ed25519_payload(private_key: Ed25519PrivateKey, payload: bytes) -> str:
    signature = private_key.sign(payload)
    return base64.b64encode(signature).decode("ascii")


def test_bootstrap_admin_session_recognized_by_protected_endpoint():
    app, TestingSessionLocal, settings, engine = get_test_setup()
    try:
        po_priv, po_bytes = generate_ed25519_keypair()
        sr_priv, sr_bytes = generate_ed25519_keypair()
        backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

        env = "development"
        targets = ["boot-admin-1", "boot-admin-2"]

        with TestingSessionLocal() as db:
            inst = get_or_create_instance_state(db)
            now = datetime.now(timezone.utc)
            issued_dt = now - timedelta(hours=1)
            expires_dt = now + timedelta(hours=5)

            payload_data = {
                "action": "bootstrap_initial_admins",
                "environment": env,
                "target_subs": targets,
                "instance_id": inst.instance_id,
                "request_id": str(uuid.uuid4()),
                "operator_id": "synthetic-operator-1",
                "issued_at": issued_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "expires_at": expires_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            canonical_bytes = create_canonical_payload(
                payload_data["environment"],
                payload_data["target_subs"],
                instance_id=payload_data["instance_id"],
                request_id=payload_data["request_id"],
                operator_id=payload_data["operator_id"],
                issued_at=payload_data["issued_at"],
                expires_at=payload_data["expires_at"],
            )
            po_sig_b64 = sign_ed25519_payload(po_priv, canonical_bytes)
            sr_sig_b64 = sign_ed25519_payload(sr_priv, canonical_bytes)

            u1 = User(
                id="boot-u1",
                sub="boot-admin-1",
                email="boot1@example.com",
                name="Bootstrap Admin 1",
                is_active=True,
            )
            u2 = User(
                id="boot-u2",
                sub="boot-admin-2",
                email="boot2@example.com",
                name="Bootstrap Admin 2",
                is_active=True,
            )
            db.add_all([u1, u2])
            db.commit()

            receipt = bootstrap_initial_admins(
                db,
                payload_data=payload_data,
                approvals={
                    "project_owner": po_sig_b64,
                    "security_reviewer": sr_sig_b64,
                },
                now=now,
                _registry_backend=backend,
            )
            assert receipt is not None

            # Create and validate session for bootstrapped admin 1
            sess = create_session(db, u1.id, settings)
            _, _, roles = validate_session(db, sess.id, settings)
            assert "system_admin" in roles
            assert Role.SYSTEM_ADMIN.value in roles

        client = TestClient(app)
        client.cookies.set("pmis_session", sess.id)
        resp = client.get("/api/v1/auth/roles/system-admin/requests")
        assert resp.status_code == 200
        data = resp.json()
        assert "requests" in data
    finally:
        engine.dispose()


def test_system_admin_approval_atomic_rollback_on_fault_injection():
    """Verify atomicity: injected failure during approval commit rolls back
    role, sessions, and request.

    Account for approver heartbeat commit in validate_session() as pre-transaction.
    Database dialect: SQLite in-memory (StaticPool). Demonstrates transaction rollback boundary.
    """
    app, TestingSessionLocal, settings, engine = get_test_setup()
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

            sess1 = create_session(db, admin1.id, settings)
            sess1_id = sess1.id
            sess1_csrf = sess1.csrf_token
            sess2 = create_session(db, admin2.id, settings)
            sess2_id = sess2.id
            sess2_csrf = sess2.csrf_token
            sess_u = create_session(db, user1.id, settings)
            user_sess_id = sess_u.id

        client = TestClient(app)
        # Admin 1 requests grant of System Admin to User 1
        client.cookies.set("pmis_session", sess1_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/grant",
            json={"target_user_id": "user1"},
            headers={"X-CSRF-Token": sess1_csrf},
        )
        assert resp.status_code in (200, 202)
        request_id = resp.json()["request_id"]

        # Hook get_db dependency to inject failure during approval commit
        from sqlalchemy.orm import Session as DBSession

        from app.database import get_db

        injection_reached = False

        def get_faulty_db():
            with DBSession(bind=engine) as session:
                real_commit = session.commit
                commit_count = 0

                def faulty_commit():
                    nonlocal commit_count, injection_reached
                    commit_count += 1
                    if commit_count == 1:
                        # 1st call is approver heartbeat in validate_session() (pre-transaction)
                        return real_commit()
                    # Subsequent commit is during approval decision!
                    # Verify that in uncommitted unit of work, role change is staged
                    flushed_role = (
                        session.query(UserRole)
                        .filter_by(user_id="user1", role=Role.SYSTEM_ADMIN)
                        .first()
                    )
                    assert flushed_role is not None
                    flushed_sess = session.query(Session).filter_by(id=user_sess_id).first()
                    assert flushed_sess.is_revoked is True
                    injection_reached = True
                    raise RuntimeError("Injected database failure during approval commit")

                session.commit = faulty_commit
                yield session

        app.dependency_overrides[get_db] = get_faulty_db

        client.cookies.set("pmis_session", sess2_id)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": request_id},
            headers={"X-CSRF-Token": sess2_csrf},
        )
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to process approval decision"
        assert injection_reached is True

        # Verify through a fresh database session that NOTHING persisted/changed
        with TestingSessionLocal() as fresh_db:
            role = (
                fresh_db.query(UserRole).filter_by(user_id="user1", role=Role.SYSTEM_ADMIN).first()
            )
            assert role is None, "Role must not be persisted on transaction rollback"

            u_sess = fresh_db.query(Session).filter_by(id=user_sess_id).first()
            assert u_sess.is_revoked is False, (
                "Target session must remain active when approval fails"
            )

            req_row = fresh_db.query(SystemAdminRequest).filter_by(id=request_id).first()
            assert req_row is not None
            assert req_row.status == "pending", "Request must remain pending"
            assert req_row.approver_id is None, "Approver ID must not be recorded"
            assert req_row.decided_at is None, "Decided timestamp must not be recorded"
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_system_admin_approval_revalidates_requester_approver_and_target():
    """Verify decision-time revalidation of requester, approver, and target preconditions."""
    app, TestingSessionLocal, settings, engine = get_test_setup()
    try:
        with TestingSessionLocal() as db:
            admin1 = User(
                id="adm_req",
                sub="s_req",
                email="req@test.com",
                name="Requester Admin",
                is_active=True,
            )
            admin2 = User(
                id="adm_app",
                sub="s_app",
                email="app@test.com",
                name="Approver Admin",
                is_active=True,
            )
            target = User(
                id="usr_tgt", sub="s_tgt", email="tgt@test.com", name="Target User", is_active=True
            )
            db.add_all([admin1, admin2, target])
            db.commit()

            db.add(
                UserRole(id="r_req", user_id="adm_req", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.add(
                UserRole(id="r_app", user_id="adm_app", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.commit()

            sess_app = create_session(db, admin2.id, settings)
            app_cookie = sess_app.id
            app_csrf = sess_app.csrf_token

        client = TestClient(app)
        client.cookies.set("pmis_session", app_cookie)

        # 1. Inactive requester at approval time
        with TestingSessionLocal() as db:
            req1 = SystemAdminRequest(
                id="req-inactive-requester",
                target_user_id="usr_tgt",
                action="grant",
                status="pending",
                requester_id="adm_req",
            )
            db.add(req1)
            # Deactivate requester
            db.query(User).filter_by(id="adm_req").update({"is_active": False})
            db.commit()

        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-inactive-requester"},
            headers={"X-CSRF-Token": app_csrf},
        )
        assert resp.status_code == 403
        with TestingSessionLocal() as db:
            r = db.query(SystemAdminRequest).filter_by(id="req-inactive-requester").first()
            assert r.status == "pending"
            assert (
                db.query(UserRole).filter_by(user_id="usr_tgt", role=Role.SYSTEM_ADMIN).first()
                is None
            )
            # Reactivate requester for subsequent tests
            db.query(User).filter_by(id="adm_req").update({"is_active": True})
            db.commit()

        # 2. De-authorized requester at approval time (lost system_admin role)
        with TestingSessionLocal() as db:
            req2 = SystemAdminRequest(
                id="req-deauth-requester",
                target_user_id="usr_tgt",
                action="grant",
                status="pending",
                requester_id="adm_req",
            )
            db.add(req2)
            db.query(UserRole).filter_by(user_id="adm_req", role=Role.SYSTEM_ADMIN).delete()
            db.commit()

        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-deauth-requester"},
            headers={"X-CSRF-Token": app_csrf},
        )
        assert resp.status_code == 403
        with TestingSessionLocal() as db:
            r = db.query(SystemAdminRequest).filter_by(id="req-deauth-requester").first()
            assert r.status == "pending"
            assert (
                db.query(UserRole).filter_by(user_id="usr_tgt", role=Role.SYSTEM_ADMIN).first()
                is None
            )
            # Re-grant admin1 system_admin role
            db.add(
                UserRole(id="r_req2", user_id="adm_req", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.commit()

        # 3. Missing target user
        with TestingSessionLocal() as db:
            req3 = SystemAdminRequest(
                id="req-missing-target",
                target_user_id="nonexistent_user",
                action="grant",
                status="pending",
                requester_id="adm_req",
            )
            db.add(req3)
            db.commit()

        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-missing-target"},
            headers={"X-CSRF-Token": app_csrf},
        )
        assert resp.status_code == 404
        with TestingSessionLocal() as db:
            r = db.query(SystemAdminRequest).filter_by(id="req-missing-target").first()
            assert r.status == "pending"

        # 4. Stale grant: target user already has System Admin role
        with TestingSessionLocal() as db:
            req4 = SystemAdminRequest(
                id="req-stale-grant",
                target_user_id="usr_tgt",
                action="grant",
                status="pending",
                requester_id="adm_req",
            )
            db.add(req4)
            db.add(
                UserRole(id="r_tgt", user_id="usr_tgt", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.commit()

        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-stale-grant"},
            headers={"X-CSRF-Token": app_csrf},
        )
        assert resp.status_code == 409
        with TestingSessionLocal() as db:
            r = db.query(SystemAdminRequest).filter_by(id="req-stale-grant").first()
            assert r.status == "pending"

        # 5. Stale revoke: target user does not have System Admin role to revoke
        with TestingSessionLocal() as db:
            # Remove target's role
            db.query(UserRole).filter_by(user_id="usr_tgt", role=Role.SYSTEM_ADMIN).delete()
            req5 = SystemAdminRequest(
                id="req-stale-revoke",
                target_user_id="usr_tgt",
                action="revoke",
                status="pending",
                requester_id="adm_req",
            )
            db.add(req5)
            db.commit()

        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-stale-revoke"},
            headers={"X-CSRF-Token": app_csrf},
        )
        assert resp.status_code == 409
        with TestingSessionLocal() as db:
            r = db.query(SystemAdminRequest).filter_by(id="req-stale-revoke").first()
            assert r.status == "pending"
    finally:
        engine.dispose()


def test_system_admin_approval_revalidates_approver_authority_during_decision(monkeypatch):
    """Verify decision-time revalidation fails closed when approver authority changes.

    Exercises case where approver state changes after session validation.
    """
    app, TestingSessionLocal, settings, engine = get_test_setup()
    try:
        with TestingSessionLocal() as db:
            admin1 = User(
                id="adm_req",
                sub="s_req",
                email="req@test.com",
                name="Requester Admin",
                is_active=True,
            )
            admin2 = User(
                id="adm_app",
                sub="s_app",
                email="app@test.com",
                name="Approver Admin",
                is_active=True,
            )
            target = User(
                id="usr_tgt",
                sub="s_tgt",
                email="tgt@test.com",
                name="Target User",
                is_active=True,
            )
            db.add_all([admin1, admin2, target])
            db.commit()

            db.add(
                UserRole(id="r_req", user_id="adm_req", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.add(
                UserRole(id="r_app", user_id="adm_app", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.commit()

            sess_app = create_session(db, admin2.id, settings)
            app_cookie = sess_app.id
            app_csrf = sess_app.csrf_token

            target_sess = create_session(db, target.id, settings)
            target_sess_id = target_sess.id

        client = TestClient(app)
        client.cookies.set("pmis_session", app_cookie)

        import app.auth.routes as auth_routes

        real_validate_session = auth_routes.validate_session
        post_validate_hook = None

        def wrapped_validate_session(db, session_id, settings_arg):
            session, actor_user, actor_roles = real_validate_session(db, session_id, settings_arg)
            if post_validate_hook:
                post_validate_hook()
            return session, actor_user, actor_roles

        monkeypatch.setattr(auth_routes, "validate_session", wrapped_validate_session)

        # 1. Approver account is made inactive after validate_session() returns
        with TestingSessionLocal() as db:
            req1 = SystemAdminRequest(
                id="req-approver-inactive",
                target_user_id="usr_tgt",
                action="grant",
                status="pending",
                requester_id="adm_req",
            )
            db.add(req1)
            db.commit()

        def deactivate_approver():
            with TestingSessionLocal() as mutate_db:
                mutate_db.query(User).filter_by(id="adm_app").update({"is_active": False})
                mutate_db.commit()

        post_validate_hook = deactivate_approver

        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-approver-inactive"},
            headers={"X-CSRF-Token": app_csrf},
        )
        assert resp.status_code == 403
        with TestingSessionLocal() as db:
            r = db.query(SystemAdminRequest).filter_by(id="req-approver-inactive").first()
            assert r.status == "pending"
            assert (
                db.query(UserRole).filter_by(user_id="usr_tgt", role=Role.SYSTEM_ADMIN).first()
                is None
            )
            tgt_s = db.query(Session).filter_by(id=target_sess_id).first()
            assert tgt_s is not None
            assert tgt_s.is_revoked is False

            # Restore synthetic approver state between scenarios
            db.query(User).filter_by(id="adm_app").update({"is_active": True})
            db.commit()

        # 2. Approver loses System Admin role after validate_session() returns
        with TestingSessionLocal() as db:
            req2 = SystemAdminRequest(
                id="req-approver-deauth",
                target_user_id="usr_tgt",
                action="grant",
                status="pending",
                requester_id="adm_req",
            )
            db.add(req2)
            db.commit()

        def deauth_approver():
            with TestingSessionLocal() as mutate_db:
                mutate_db.query(UserRole).filter_by(
                    user_id="adm_app", role=Role.SYSTEM_ADMIN
                ).delete()
                mutate_db.commit()

        post_validate_hook = deauth_approver

        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-approver-deauth"},
            headers={"X-CSRF-Token": app_csrf},
        )
        assert resp.status_code == 403
        with TestingSessionLocal() as db:
            r = db.query(SystemAdminRequest).filter_by(id="req-approver-deauth").first()
            assert r.status == "pending"
            assert (
                db.query(UserRole).filter_by(user_id="usr_tgt", role=Role.SYSTEM_ADMIN).first()
                is None
            )
            tgt_s = db.query(Session).filter_by(id=target_sess_id).first()
            assert tgt_s is not None
            assert tgt_s.is_revoked is False

            # Restore synthetic approver state between scenarios
            db.add(
                UserRole(
                    id="r_app_restored",
                    user_id="adm_app",
                    role=Role.SYSTEM_ADMIN,
                    granted_by="seed",
                )
            )
            db.commit()
    finally:
        engine.dispose()


def test_legacy_role_requester_cannot_authorize_approval():
    """Verify a requester with only legacy 'System Admin' row cannot authorize approval.

    Behavior 1:
    A canonical requester creates a request, then loses the canonical role and receives only
    a legacy 'System Admin' row. A different currently authorized canonical admin attempts
    approval; approval is rejected (403) and the request remains pending with no target
    role or session side effect.
    """
    app, TestingSessionLocal, settings, engine = get_test_setup()
    try:
        with TestingSessionLocal() as db:
            admin1 = User(
                id="adm_req",
                sub="s_req",
                email="req@test.com",
                name="Requester Admin",
                is_active=True,
            )
            admin2 = User(
                id="adm_app",
                sub="s_app",
                email="app@test.com",
                name="Approver Admin",
                is_active=True,
            )
            target = User(
                id="usr_tgt",
                sub="s_tgt",
                email="tgt@test.com",
                name="Target User",
                is_active=True,
            )
            db.add_all([admin1, admin2, target])
            db.commit()

            db.add(
                UserRole(id="r_req", user_id="adm_req", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.add(
                UserRole(id="r_app", user_id="adm_app", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.commit()

            sess_app = create_session(db, admin2.id, settings)
            app_cookie = sess_app.id
            app_csrf = sess_app.csrf_token

            target_sess = create_session(db, target.id, settings)
            target_sess_id = target_sess.id

            req = SystemAdminRequest(
                id="req-legacy-requester",
                target_user_id="usr_tgt",
                action="grant",
                status="pending",
                requester_id="adm_req",
            )
            db.add(req)
            db.commit()

            # Requester loses canonical role and receives only legacy 'System Admin' row
            db.query(UserRole).filter_by(user_id="adm_req", role=Role.SYSTEM_ADMIN).delete()
            db.add(
                UserRole(
                    id="r_req_legacy",
                    user_id="adm_req",
                    role="System Admin",
                    granted_by="seed",
                )
            )
            db.commit()

        client = TestClient(app)
        client.cookies.set("pmis_session", app_cookie)

        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-legacy-requester"},
            headers={"X-CSRF-Token": app_csrf},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Requester is no longer an active System Admin"

        with TestingSessionLocal() as db:
            r = db.query(SystemAdminRequest).filter_by(id="req-legacy-requester").first()
            assert r is not None
            assert r.status == "pending"
            assert r.approver_id is None
            assert r.decided_at is None
            assert (
                db.query(UserRole).filter_by(user_id="usr_tgt", role=Role.SYSTEM_ADMIN).first()
                is None
            )
            tgt_s = db.query(Session).filter_by(id=target_sess_id).first()
            assert tgt_s is not None
            assert tgt_s.is_revoked is False
    finally:
        engine.dispose()


def test_legacy_role_approver_cannot_authorize_approval(monkeypatch):
    """Verify a legacy-only approver cannot establish decision authority.

    Behavior 2:
    A legacy-only approver cannot establish decision authority even when the request
    is otherwise pending; verify state remains unchanged.
    Tests both:
    - Approver with only legacy 'System Admin' row at session time
    - Approver whose canonical role is swapped to legacy 'System Admin' during decision time
    """
    app, TestingSessionLocal, settings, engine = get_test_setup()
    try:
        with TestingSessionLocal() as db:
            admin1 = User(
                id="adm_req",
                sub="s_req",
                email="req@test.com",
                name="Requester Admin",
                is_active=True,
            )
            admin2 = User(
                id="adm_app",
                sub="s_app",
                email="app@test.com",
                name="Approver Admin",
                is_active=True,
            )
            admin_legacy = User(
                id="adm_leg",
                sub="s_leg",
                email="leg@test.com",
                name="Legacy Admin",
                is_active=True,
            )
            target = User(
                id="usr_tgt",
                sub="s_tgt",
                email="tgt@test.com",
                name="Target User",
                is_active=True,
            )
            db.add_all([admin1, admin2, admin_legacy, target])
            db.commit()

            db.add(
                UserRole(id="r_req", user_id="adm_req", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.add(
                UserRole(id="r_app", user_id="adm_app", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.add(
                UserRole(
                    id="r_leg",
                    user_id="adm_leg",
                    role="System Admin",
                    granted_by="seed",
                )
            )
            db.commit()

            sess_app = create_session(db, admin2.id, settings)
            app_cookie = sess_app.id
            app_csrf = sess_app.csrf_token

            sess_leg = create_session(db, admin_legacy.id, settings)
            leg_cookie = sess_leg.id
            leg_csrf = sess_leg.csrf_token

            target_sess = create_session(db, target.id, settings)
            target_sess_id = target_sess.id

            req1 = SystemAdminRequest(
                id="req-legacy-approver-static",
                target_user_id="usr_tgt",
                action="grant",
                status="pending",
                requester_id="adm_req",
            )
            req2 = SystemAdminRequest(
                id="req-legacy-approver-dynamic",
                target_user_id="usr_tgt",
                action="grant",
                status="pending",
                requester_id="adm_req",
            )
            db.add_all([req1, req2])
            db.commit()

        # Case 2A: Approver with only legacy row attempts approval
        leg_client = TestClient(app)
        leg_client.cookies.set("pmis_session", leg_cookie)
        resp_leg = leg_client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-legacy-approver-static"},
            headers={"X-CSRF-Token": leg_csrf},
        )
        assert resp_leg.status_code == 403
        with TestingSessionLocal() as db:
            r1 = db.query(SystemAdminRequest).filter_by(id="req-legacy-approver-static").first()
            assert r1 is not None
            assert r1.status == "pending"
            assert r1.approver_id is None
            assert (
                db.query(UserRole).filter_by(user_id="usr_tgt", role=Role.SYSTEM_ADMIN).first()
                is None
            )

        # Case 2B: Approver's canonical role transitions to legacy-only at decision time
        import app.auth.routes as auth_routes

        real_validate_session = auth_routes.validate_session
        swap_hook_active = False

        def wrapped_validate_session(db, session_id, settings_arg):
            session, actor_user, actor_roles = real_validate_session(db, session_id, settings_arg)
            if swap_hook_active:
                with TestingSessionLocal() as mutate_db:
                    mutate_db.query(UserRole).filter_by(
                        user_id="adm_app", role=Role.SYSTEM_ADMIN
                    ).delete()
                    mutate_db.add(
                        UserRole(
                            id="r_app_legacy",
                            user_id="adm_app",
                            role="System Admin",
                            granted_by="seed",
                        )
                    )
                    mutate_db.commit()
            return session, actor_user, actor_roles

        monkeypatch.setattr(auth_routes, "validate_session", wrapped_validate_session)
        swap_hook_active = True

        client = TestClient(app)
        client.cookies.set("pmis_session", app_cookie)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-legacy-approver-dynamic"},
            headers={"X-CSRF-Token": app_csrf},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Approver must be an active System Admin"

        with TestingSessionLocal() as db:
            r2 = db.query(SystemAdminRequest).filter_by(id="req-legacy-approver-dynamic").first()
            assert r2 is not None
            assert r2.status == "pending"
            assert r2.approver_id is None
            assert r2.decided_at is None
            assert (
                db.query(UserRole).filter_by(user_id="usr_tgt", role=Role.SYSTEM_ADMIN).first()
                is None
            )
            tgt_s = db.query(Session).filter_by(id=target_sess_id).first()
            assert tgt_s is not None
            assert tgt_s.is_revoked is False
    finally:
        engine.dispose()


def test_legacy_role_canonical_requester_and_approver_succeed_under_hg2():
    """Verify canonical requester and approver continue to work under existing HG2 policy.

    Behavior 3:
    Canonical current requester and approver continue to work under the existing HG2 policy.
    """
    app, TestingSessionLocal, settings, engine = get_test_setup()
    try:
        with TestingSessionLocal() as db:
            admin1 = User(
                id="adm_req",
                sub="s_req",
                email="req@test.com",
                name="Requester Admin",
                is_active=True,
            )
            admin2 = User(
                id="adm_app",
                sub="s_app",
                email="app@test.com",
                name="Approver Admin",
                is_active=True,
            )
            target = User(
                id="usr_tgt",
                sub="s_tgt",
                email="tgt@test.com",
                name="Target User",
                is_active=True,
            )
            db.add_all([admin1, admin2, target])
            db.commit()

            db.add(
                UserRole(id="r_req", user_id="adm_req", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.add(
                UserRole(id="r_app", user_id="adm_app", role=Role.SYSTEM_ADMIN, granted_by="seed")
            )
            db.commit()

            sess_app = create_session(db, admin2.id, settings)
            app_cookie = sess_app.id
            app_csrf = sess_app.csrf_token

            target_sess = create_session(db, target.id, settings)
            target_sess_id = target_sess.id

            req = SystemAdminRequest(
                id="req-canonical-hg2",
                target_user_id="usr_tgt",
                action="grant",
                status="pending",
                requester_id="adm_req",
            )
            db.add(req)
            db.commit()

        client = TestClient(app)
        client.cookies.set("pmis_session", app_cookie)
        resp = client.post(
            "/api/v1/auth/roles/system-admin/approve",
            json={"request_id": "req-canonical-hg2"},
            headers={"X-CSRF-Token": app_csrf},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"
        assert data["request_id"] == "req-canonical-hg2"

        with TestingSessionLocal() as db:
            r = db.query(SystemAdminRequest).filter_by(id="req-canonical-hg2").first()
            assert r is not None
            assert r.status == "approved"
            assert r.approver_id == "adm_app"
            assert r.decided_at is not None
            granted_role = (
                db.query(UserRole).filter_by(user_id="usr_tgt", role=Role.SYSTEM_ADMIN).first()
            )
            assert granted_role is not None
            assert granted_role.role == Role.SYSTEM_ADMIN.value
            tgt_s = db.query(Session).filter_by(id=target_sess_id).first()
            assert tgt_s is not None
            assert tgt_s.is_revoked is True
    finally:
        engine.dispose()


def test_legacy_role_blocks_bootstrap_guard():
    """Verify bootstrap guard continues to detect legacy rows and block bootstrap.

    Behavior 4:
    Bootstrap guard continues to detect legacy rows as a reason to block bootstrap;
    do not migrate them into authority.
    """
    app, TestingSessionLocal, settings, engine = get_test_setup()
    try:
        po_priv, po_bytes = generate_ed25519_keypair()
        sr_priv, sr_bytes = generate_ed25519_keypair()
        backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

        with TestingSessionLocal() as db:
            inst = get_or_create_instance_state(db)
            legacy_user = User(
                id="u_legacy",
                sub="s_legacy",
                email="legacy@test.com",
                name="Legacy User",
                is_active=True,
            )
            db.add(legacy_user)
            db.commit()

            # Insert inert legacy display-value System Admin row
            db.add(
                UserRole(
                    id="r_legacy_guard",
                    user_id="u_legacy",
                    role="System Admin",
                    granted_by="seed",
                )
            )
            db.commit()

            now = datetime.now(timezone.utc)
            payload_data = {
                "action": "bootstrap_initial_admins",
                "environment": "development",
                "target_subs": ["boot-admin-1", "boot-admin-2"],
                "instance_id": inst.instance_id,
                "request_id": str(uuid.uuid4()),
                "operator_id": "synthetic-operator-1",
                "issued_at": (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "expires_at": (now + timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            canonical_bytes = create_canonical_payload(
                payload_data["environment"],
                payload_data["target_subs"],
                instance_id=payload_data["instance_id"],
                request_id=payload_data["request_id"],
                operator_id=payload_data["operator_id"],
                issued_at=payload_data["issued_at"],
                expires_at=payload_data["expires_at"],
            )
            po_sig_b64 = sign_ed25519_payload(po_priv, canonical_bytes)
            sr_sig_b64 = sign_ed25519_payload(sr_priv, canonical_bytes)

            with pytest.raises(BootstrapError, match="System Admin already exists"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={
                        "project_owner": po_sig_b64,
                        "security_reviewer": sr_sig_b64,
                    },
                    now=now,
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()
