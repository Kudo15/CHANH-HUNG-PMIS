import json
import time
from unittest.mock import MagicMock, patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.models import OIDCState, Session, User
from app.auth.oidc import MockOIDCClient, StaticKeyResolver
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
        session_cookie_secure=True,
    )
    app = create_app(settings)
    app.state.engine = engine
    priv_key, pub_pem = generate_rsa_key_pair()
    resolver = StaticKeyResolver({"test-key-1": pub_pem})
    app.state.key_resolver = resolver
    app.state.priv_key = priv_key
    return app, TestingSessionLocal, settings, engine


def test_no_local_password_or_registration_endpoints():
    app, _, _, engine = get_test_setup()
    try:
        # Check database columns on User
        columns = [c.name for c in User.__table__.columns]
        assert "password" not in columns
        assert "password_hash" not in columns
        assert "hashed_password" not in columns

        # Check routes for registration / local password
        route_paths = []
        for r in app.routes:
            if isinstance(r, APIRoute):
                route_paths.append(r.path)
            elif hasattr(r, "routes"):
                for sub_r in getattr(r, "routes", []):
                    if isinstance(sub_r, APIRoute):
                        route_paths.append(sub_r.path)

        assert "/register" not in route_paths
        assert "/api/v1/auth/register" not in route_paths
        assert "/api/v1/auth/password" not in route_paths
        assert "/api/v1/auth/reset-password" not in route_paths
    finally:
        engine.dispose()


def test_login_redirects_with_state_and_nonce():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        client = TestClient(app)
        response = client.get("/api/v1/auth/login", follow_redirects=False)
        assert response.status_code in (302, 303, 307)
        location = response.headers["location"]
        assert "https://idp.example.com/oauth/authorize" in location
        assert "response_type=code" in location
        assert "client_id=pmis-app" in location
        assert "state=" in location
        assert "nonce=" in location

        # Verify state is persisted in DB
        with SessionLocal() as db:
            states = db.query(OIDCState).all()
            assert len(states) == 1
            assert states[0].state in location
            assert states[0].nonce in location
    finally:
        engine.dispose()


def test_callback_rejects_missing_or_invalid_state():
    app, SessionLocal, _, engine = get_test_setup()
    try:
        client = TestClient(app)
        # Missing state
        resp1 = client.get("/api/v1/auth/callback?code=some-code")
        assert resp1.status_code in (400, 401, 422)

        # Invalid state
        resp2 = client.get("/api/v1/auth/callback?code=some-code&state=nonexistent")
        assert resp2.status_code in (400, 401)
    finally:
        engine.dispose()


def test_callback_rejects_expired_state():
    app, SessionLocal, _, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            expired_state = OIDCState(
                state="exp-state",
                nonce="exp-nonce",
                redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                created_at=time.time() - 1000,
                expires_at=time.time() - 100,
            )
            db.add(expired_state)
            db.commit()

        client = TestClient(app)
        resp = client.get("/api/v1/auth/callback?code=some-code&state=exp-state")
        assert resp.status_code in (400, 401)
    finally:
        engine.dispose()


def test_callback_validates_token_claims_and_fails_closed():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        # Pre-seed state
        with SessionLocal() as db:
            valid_state = OIDCState(
                state="valid-state-1",
                nonce="expected-nonce",
                redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                created_at=time.time(),
                expires_at=time.time() + 600,
            )
            db.add(valid_state)
            db.commit()

        mock_oidc = MockOIDCClient()
        app.state.oidc_client = mock_oidc

        client = TestClient(app)

        # 1. Invalid issuer
        token_iss = make_signed_token(
            {
                "iss": "https://wrong-idp.com",
                "aud": "pmis-app",
                "sub": "user-123",
                "nonce": "expected-nonce",
                "exp": time.time() + 3600,
                "email": "user@example.com",
                "name": "User One",
            },
            app.state.priv_key,
        )
        mock_oidc.set_mock_id_token(token_iss)
        resp_iss = client.get("/api/v1/auth/callback?code=code1&state=valid-state-1")
        assert resp_iss.status_code in (400, 401)

        # Re-add state for next test
        with SessionLocal() as db:
            db.merge(
                OIDCState(
                    state="valid-state-2",
                    nonce="expected-nonce",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                )
            )
            db.commit()

        # 2. Invalid audience
        token_aud = make_signed_token(
            {
                "iss": "https://idp.example.com",
                "aud": "wrong-client-id",
                "sub": "user-123",
                "nonce": "expected-nonce",
                "exp": time.time() + 3600,
                "email": "user@example.com",
                "name": "User One",
            },
            app.state.priv_key,
        )
        mock_oidc.set_mock_id_token(token_aud)
        resp_aud = client.get("/api/v1/auth/callback?code=code2&state=valid-state-2")
        assert resp_aud.status_code in (400, 401)

        # 3. Expired token
        with SessionLocal() as db:
            db.merge(
                OIDCState(
                    state="valid-state-3",
                    nonce="expected-nonce",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                )
            )
            db.commit()
        token_exp = make_signed_token(
            {
                "iss": "https://idp.example.com",
                "aud": "pmis-app",
                "sub": "user-123",
                "nonce": "expected-nonce",
                "exp": time.time() - 3600,
                "email": "user@example.com",
                "name": "User One",
            },
            app.state.priv_key,
        )
        mock_oidc.set_mock_id_token(token_exp)
        resp_exp = client.get("/api/v1/auth/callback?code=code3&state=valid-state-3")
        assert resp_exp.status_code in (400, 401)

        # 4. Nonce mismatch
        with SessionLocal() as db:
            db.merge(
                OIDCState(
                    state="valid-state-4",
                    nonce="expected-nonce",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                )
            )
            db.commit()
        token_nonce = make_signed_token(
            {
                "iss": "https://idp.example.com",
                "aud": "pmis-app",
                "sub": "user-123",
                "nonce": "tampered-nonce",
                "exp": time.time() + 3600,
                "email": "user@example.com",
                "name": "User One",
            },
            app.state.priv_key,
        )
        mock_oidc.set_mock_id_token(token_nonce)
        resp_nonce = client.get("/api/v1/auth/callback?code=code4&state=valid-state-4")
        assert resp_nonce.status_code in (400, 401)
    finally:
        engine.dispose()


def test_callback_rejects_deprovisioned_user():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        # Pre-seed inactive user
        with SessionLocal() as db:
            user = User(
                id="u-deprov",
                sub="sub-deprov-999",
                email="deprov@example.com",
                name="Deprovisioned User",
                department="Legal",
                is_active=False,
            )
            db.add(user)
            db.add(
                OIDCState(
                    state="state-deprov",
                    nonce="nonce-deprov",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                )
            )
            db.commit()

        mock_oidc = MockOIDCClient()
        token_deprov = make_signed_token(
            {
                "iss": "https://idp.example.com",
                "aud": "pmis-app",
                "sub": "sub-deprov-999",
                "nonce": "nonce-deprov",
                "exp": time.time() + 3600,
                "email": "deprov@example.com",
                "name": "Deprovisioned User",
            },
            app.state.priv_key,
        )
        mock_oidc.set_mock_id_token(token_deprov)
        app.state.oidc_client = mock_oidc

        client = TestClient(app)
        resp = client.get("/api/v1/auth/callback?code=deprov-code&state=state-deprov")
        assert resp.status_code == 403
    finally:
        engine.dispose()


def test_callback_success_creates_session_and_sets_cookies():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            db.add(
                OIDCState(
                    state="success-state",
                    nonce="success-nonce",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                )
            )
            db.commit()

        mock_oidc = MockOIDCClient()
        token_alice = make_signed_token(
            {
                "iss": "https://idp.example.com",
                "aud": "pmis-app",
                "sub": "sub-alice",
                "nonce": "success-nonce",
                "exp": time.time() + 3600,
                "email": "alice@example.com",
                "name": "Alice Wonderland",
                "department": "Engineering",
            },
            app.state.priv_key,
        )
        mock_oidc.set_mock_id_token(token_alice)
        app.state.oidc_client = mock_oidc

        client = TestClient(app)
        resp = client.get(
            "/api/v1/auth/callback?code=alice-code&state=success-state", follow_redirects=False
        )
        assert resp.status_code in (200, 302, 303)

        # Check cookies
        cookies = resp.cookies
        assert "pmis_session" in cookies
        assert "pmis_csrf" in cookies

        # State should be removed/consumed (one-time use)
        with SessionLocal() as db:
            st = db.query(OIDCState).filter_by(state="success-state").first()
            assert st is None
            user = db.query(User).filter_by(sub="sub-alice").first()
            assert user is not None
            assert user.email == "alice@example.com"
            assert user.name == "Alice Wonderland"
            assert user.department == "Engineering"
            assert user.is_active is True

            sessions = db.query(Session).filter_by(user_id=user.id).all()
            assert len(sessions) == 1
            assert sessions[0].is_revoked is False
    finally:
        engine.dispose()


def test_callback_with_default_oidc_client_success():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            db.add(
                OIDCState(
                    state="default-client-state",
                    nonce="default-client-nonce",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                )
            )
            db.commit()

        token_bob = make_signed_token(
            {
                "iss": "https://idp.example.com",
                "aud": "pmis-app",
                "sub": "sub-bob-default",
                "nonce": "default-client-nonce",
                "exp": time.time() + 3600,
                "email": "bob@example.com",
                "name": "Bob Builder",
                "department": "Security",
            },
            app.state.priv_key,
        )

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "access_token": "mock-token",
                "id_token": token_bob,
                "token_type": "Bearer",
            }
        ).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = None

        # Do not set app.state.oidc_client; let process_callback use DefaultOIDCClient
        if hasattr(app.state, "oidc_client"):
            delattr(app.state, "oidc_client")

        client = TestClient(app)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            resp = client.get(
                "/api/v1/auth/callback?code=bob-code&state=default-client-state",
                follow_redirects=False,
            )

        assert resp.status_code in (200, 302, 303)
        assert "pmis_session" in resp.cookies
        with SessionLocal() as db:
            user = db.query(User).filter_by(sub="sub-bob-default").first()
            assert user is not None
            assert user.email == "bob@example.com"
            assert user.name == "Bob Builder"
    finally:
        engine.dispose()
