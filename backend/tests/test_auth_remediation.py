import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.models import OIDCState, Session, SystemAdminRequest, User, UserRole
from app.auth.oidc import (
    StaticKeyResolver,
    decode_and_verify_id_token,
    initiate_login,
)
from app.auth.policy import Role
from app.auth.session import create_session
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
