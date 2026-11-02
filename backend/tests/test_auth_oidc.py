import base64
import hashlib
import json
import time
import urllib.parse
import urllib.request
from unittest.mock import MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.models import OIDCState, Session, User
from app.auth.oidc import (
    DefaultOIDCClient,
    MockOIDCClient,
    StaticKeyResolver,
    process_callback,
)
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
        raw_cookie = "deprov-browser-cookie-12345"
        binding_digest = hashlib.sha256(raw_cookie.encode("utf-8")).hexdigest()
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
                    code_verifier="deprov-verifier-12345678901234567890",
                    binding_digest=binding_digest,
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

        client = TestClient(app, base_url="https://testserver")
        client.cookies.set("pmis_oidc_bind", raw_cookie)
        resp = client.get("/api/v1/auth/callback?code=deprov-code&state=state-deprov")
        assert resp.status_code == 403
    finally:
        engine.dispose()


def test_callback_success_creates_session_and_sets_cookies():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        raw_cookie = "success-browser-cookie-12345"
        binding_digest = hashlib.sha256(raw_cookie.encode("utf-8")).hexdigest()
        with SessionLocal() as db:
            db.add(
                OIDCState(
                    state="success-state",
                    nonce="success-nonce",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                    code_verifier="success-verifier-12345678901234567890",
                    binding_digest=binding_digest,
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

        client = TestClient(app, base_url="https://testserver")
        client.cookies.set("pmis_oidc_bind", raw_cookie)
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
        raw_cookie = "default-client-browser-cookie-12345"
        binding_digest = hashlib.sha256(raw_cookie.encode("utf-8")).hexdigest()
        with SessionLocal() as db:
            db.add(
                OIDCState(
                    state="default-client-state",
                    nonce="default-client-nonce",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                    code_verifier="default-client-verifier-12345678901234567890",
                    binding_digest=binding_digest,
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

        client = TestClient(app, base_url="https://testserver")
        client.cookies.set("pmis_oidc_bind", raw_cookie)
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


def test_login_sets_s256_pkce_and_browser_binding_cookie():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        client = TestClient(app)
        response = client.get("/api/v1/auth/login", follow_redirects=False)
        assert response.status_code in (302, 303, 307)
        location = response.headers["location"]
        parsed = urllib.parse.urlparse(location)
        params = urllib.parse.parse_qs(parsed.query)

        assert "code_challenge" in params
        assert params.get("code_challenge_method") == ["S256"]
        assert "code_verifier" not in params
        challenge = params["code_challenge"][0]

        # Verify browser-binding cookie is set on redirect response
        cookies = response.cookies
        assert "pmis_oidc_bind" in cookies
        raw_cookie = cookies["pmis_oidc_bind"]
        assert len(raw_cookie) >= 32

        # Verify cookie header attributes: HttpOnly, Secure, SameSite=Lax, Path=/
        set_cookie_header = response.headers.get("set-cookie", "")
        assert "pmis_oidc_bind" in set_cookie_header
        assert "HttpOnly" in set_cookie_header or "httponly" in set_cookie_header.lower()
        assert "Secure" in set_cookie_header or "secure" in set_cookie_header.lower()
        assert "samesite=lax" in set_cookie_header.lower()

        # Verify database persistence: verifier and binding digest stored, raw cookie NOT stored
        with SessionLocal() as db:
            st = db.query(OIDCState).filter_by(state=params["state"][0]).first()
            assert st is not None
            assert hasattr(st, "code_verifier")
            assert hasattr(st, "binding_digest")
            assert st.code_verifier is not None
            assert st.binding_digest is not None
            assert st.code_verifier not in location
            assert raw_cookie != st.binding_digest
            expected_digest = hashlib.sha256(raw_cookie.encode("utf-8")).hexdigest()
            assert st.binding_digest == expected_digest

            # Check challenge matches verifier using S256 (base64url without padding)
            verifier_hash = hashlib.sha256(st.code_verifier.encode("ascii")).digest()
            expected_challenge = base64.urlsafe_b64encode(verifier_hash).decode("ascii").rstrip("=")
            assert challenge == expected_challenge
    finally:
        engine.dispose()


def test_callback_rejects_missing_or_mismatched_browser_binding():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        mock_client = MagicMock()
        app.state.oidc_client = mock_client

        raw_cookie = "valid-browser-token-12345678901234567890"
        digest = hashlib.sha256(raw_cookie.encode("utf-8")).hexdigest()

        with SessionLocal() as db:
            db.add(
                OIDCState(
                    state="bind-test-state-1",
                    nonce="bind-test-nonce-1",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                    code_verifier="test-pkce-verifier-12345678901234567890",
                    binding_digest=digest,
                )
            )
            db.commit()

        client = TestClient(app)
        # 1. Callback without binding cookie: must be rejected before exchange
        resp_no_cookie = client.get(
            "/api/v1/auth/callback?code=some-code&state=bind-test-state-1",
            follow_redirects=False,
        )
        assert resp_no_cookie.status_code == 400
        assert mock_client.exchange_code.call_count == 0
        with SessionLocal() as db:
            assert db.query(OIDCState).filter_by(state="bind-test-state-1").first() is not None

        # Re-add state with fresh state
        with SessionLocal() as db:
            db.merge(
                OIDCState(
                    state="bind-test-state-2",
                    nonce="bind-test-nonce-2",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                    code_verifier="test-pkce-verifier-12345678901234567890",
                    binding_digest=digest,
                )
            )
            db.commit()

        # 2. Callback with mismatched cookie: must be rejected before exchange
        client.cookies.set("pmis_oidc_bind", "tampered-wrong-cookie-value")
        resp_mismatch = client.get(
            "/api/v1/auth/callback?code=some-code&state=bind-test-state-2",
            follow_redirects=False,
        )
        assert resp_mismatch.status_code == 400
        assert mock_client.exchange_code.call_count == 0
        with SessionLocal() as db:
            assert db.query(OIDCState).filter_by(state="bind-test-state-2").first() is not None
    finally:
        engine.dispose()


def test_callback_rejects_legacy_state_missing_pkce_or_binding():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        mock_client = MagicMock()
        app.state.oidc_client = mock_client

        with SessionLocal() as db:
            db.add(
                OIDCState(
                    state="legacy-state-1",
                    nonce="legacy-nonce-1",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                    code_verifier=None,
                    binding_digest=None,
                )
            )
            db.commit()

        client = TestClient(app)
        client.cookies.set("pmis_oidc_bind", "some-cookie")
        resp = client.get(
            "/api/v1/auth/callback?code=some-code&state=legacy-state-1",
            follow_redirects=False,
        )
        assert resp.status_code == 400
        assert mock_client.exchange_code.call_count == 0
    finally:
        engine.dispose()


def test_callback_browser_swapping_rejected_and_different_client_cannot_redeem():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        mock_client = MagicMock()
        app.state.oidc_client = mock_client

        # Browser 1 (Browser A) initiates login
        client1 = TestClient(app, base_url="https://testserver")
        resp1 = client1.get("/api/v1/auth/login", follow_redirects=False)
        assert resp1.status_code in (302, 303, 307)
        loc = resp1.headers["location"]
        state = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)["state"][0]

        with SessionLocal() as db:
            st = db.query(OIDCState).filter_by(state=state).first()
            assert st is not None
            stored_nonce = st.nonce
            stored_verifier = st.code_verifier

        # Browser 2 (Browser B) attempts to redeem Browser A's state without cookie
        client2 = TestClient(app, base_url="https://testserver")
        resp2_no_cookie = client2.get(
            f"/api/v1/auth/callback?code=stolen-code&state={state}",
            follow_redirects=False,
        )
        assert resp2_no_cookie.status_code == 400
        assert mock_client.exchange_code.call_count == 0

        # Missing/mismatched binding must NOT consume Browser A's transaction
        with SessionLocal() as db:
            assert db.query(OIDCState).filter_by(state=state).first() is not None

        # Browser 3 attempts with mismatched cookie
        client3 = TestClient(app, base_url="https://testserver")
        client3.cookies.set("pmis_oidc_bind", "attacker-browser-binding-cookie")
        resp3_mismatch = client3.get(
            f"/api/v1/auth/callback?code=stolen-code&state={state}",
            follow_redirects=False,
        )
        assert resp3_mismatch.status_code == 400
        assert mock_client.exchange_code.call_count == 0

        # Transaction still intact for legitimate Browser A
        with SessionLocal() as db:
            assert db.query(OIDCState).filter_by(state=state).first() is not None

        # Browser A completes the valid transaction
        token = make_signed_token(
            {
                "iss": "https://idp.example.com",
                "aud": "pmis-app",
                "sub": "sub-browser-a",
                "nonce": stored_nonce,
                "exp": time.time() + 3600,
                "email": "browser-a@example.com",
                "name": "Browser A User",
            },
            app.state.priv_key,
        )
        mock_client.exchange_code.return_value = {
            "access_token": "mock-access-a",
            "id_token": token,
            "token_type": "Bearer",
        }

        resp1_cb = client1.get(
            f"/api/v1/auth/callback?code=valid-code-a&state={state}",
            follow_redirects=False,
        )
        assert resp1_cb.status_code == 200
        assert resp1_cb.json()["status"] == "authenticated"
        assert "pmis_session" in resp1_cb.cookies
        mock_client.exchange_code.assert_called_once_with(
            "valid-code-a",
            settings.oidc_redirect_uri,
            code_verifier=stored_verifier,
        )

        # Atomic one-time consumption: now transaction is consumed
        with SessionLocal() as db:
            assert db.query(OIDCState).filter_by(state=state).first() is None

        # Replay attempt fails closed
        replay_resp = client1.get(
            f"/api/v1/auth/callback?code=valid-code-a&state={state}",
            follow_redirects=False,
        )
        assert replay_resp.status_code == 400
    finally:
        engine.dispose()


def test_same_browser_full_flow_clears_cookie_and_passes_verifier():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        client = TestClient(app, base_url="https://testserver")
        # 1. Login sets binding cookie and PKCE
        login_resp = client.get("/api/v1/auth/login", follow_redirects=False)
        loc = login_resp.headers["location"]
        state = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)["state"][0]

        with SessionLocal() as db:
            st = db.query(OIDCState).filter_by(state=state).first()
            assert st is not None
            stored_nonce = st.nonce
            stored_verifier = st.code_verifier

        token = make_signed_token(
            {
                "iss": "https://idp.example.com",
                "aud": "pmis-app",
                "sub": "sub-pkce-user",
                "nonce": stored_nonce,
                "exp": time.time() + 3600,
                "email": "pkce@example.com",
                "name": "PKCE User",
            },
            app.state.priv_key,
        )

        mock_client = MagicMock()
        mock_client.exchange_code.return_value = {
            "access_token": "mock-access",
            "id_token": token,
            "token_type": "Bearer",
        }
        app.state.oidc_client = mock_client

        # 2. Callback from same browser client (has cookie)
        cb_resp = client.get(
            f"/api/v1/auth/callback?code=good-code&state={state}",
            follow_redirects=False,
        )
        assert cb_resp.status_code == 200
        assert cb_resp.json()["status"] == "authenticated"
        assert "pmis_session" in cb_resp.cookies
        assert "pmis_csrf" in cb_resp.cookies

        # Verifier was passed to exchange_code
        mock_client.exchange_code.assert_called_once_with(
            "good-code",
            settings.oidc_redirect_uri,
            code_verifier=stored_verifier,
        )

        # Browser-binding cookie is cleared on successful callback
        set_cookie_headers = cb_resp.headers.get_list("set-cookie")
        binding_cleared = any(
            "pmis_oidc_bind=" in h
            and ("Max-Age=0" in h or "max-age=0" in h or "expires=" in h.lower())
            for h in set_cookie_headers
        )
        assert binding_cleared

        # State is consumed (one-time use)
        with SessionLocal() as db:
            assert db.query(OIDCState).filter_by(state=state).first() is None

        # Replay attempt fails
        replay_resp = client.get(
            f"/api/v1/auth/callback?code=good-code&state={state}",
            follow_redirects=False,
        )
        assert replay_resp.status_code == 400
    finally:
        engine.dispose()


def test_callback_atomic_claim_prevents_stale_reader_double_exchange():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        mock_client = MagicMock()
        app.state.oidc_client = mock_client

        raw_cookie = "valid-browser-token-stale-reader-test"
        digest = hashlib.sha256(raw_cookie.encode("utf-8")).hexdigest()
        state = "stale-reader-test-state"
        nonce = "stale-reader-test-nonce"
        verifier = "stale-reader-test-verifier-12345678901234567890"

        with SessionLocal() as db:
            db.add(
                OIDCState(
                    state=state,
                    nonce=nonce,
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                    code_verifier=verifier,
                    binding_digest=digest,
                )
            )
            db.commit()

        token = make_signed_token(
            {
                "iss": "https://idp.example.com",
                "aud": "pmis-app",
                "sub": "sub-stale-reader",
                "nonce": nonce,
                "exp": time.time() + 3600,
                "email": "stale@example.com",
                "name": "Stale Reader",
            },
            app.state.priv_key,
        )
        mock_client.exchange_code.return_value = {
            "access_token": "mock-access",
            "id_token": token,
            "token_type": "Bearer",
        }

        # Simulate concurrent stale reader:
        # db2 reads valid state, but another transaction claims/deletes it before db2 consumes
        with SessionLocal() as db2:
            orig_query = db2.query

            def racing_query(*args, **kwargs):
                q = orig_query(*args, **kwargs)
                if args and args[0] is OIDCState:
                    orig_first = q.first

                    def racing_first():
                        res = orig_first()
                        if res is not None:
                            # Concurrent callback claims/deletes the state before db2
                            # reaches the consumption step
                            with SessionLocal() as db_other:
                                db_other.query(OIDCState).filter(OIDCState.state == state).delete(
                                    synchronize_session=False
                                )
                                db_other.commit()
                        return res

                    q.first = racing_first  # type: ignore
                return q

            db2.query = racing_query  # type: ignore

            # Callback 2 (with stale loaded state) attempts to consume
            # Must fail closed with HTTPException(400) before token exchange,
            # NOT raise an unhandled StaleDataError or reach exchange_code
            with pytest.raises(HTTPException) as exc_info:
                process_callback(
                    db2,
                    settings,
                    code="code2",
                    state=state,
                    browser_binding_cookie=raw_cookie,
                    oidc_client=mock_client,
                    key_resolver=app.state.key_resolver,
                )
            assert exc_info.value.status_code == 400
            assert mock_client.exchange_code.call_count == 0
    finally:
        engine.dispose()


def test_callback_cookie_cleanup_on_downstream_failure_and_retention_on_pre_consumption_rejection():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        mock_client = MagicMock()
        app.state.oidc_client = mock_client

        raw_cookie = "valid-browser-token-cleanup-test"
        digest = hashlib.sha256(raw_cookie.encode("utf-8")).hexdigest()

        # Helper to check if pmis_oidc_bind cookie is cleared in response
        def is_binding_cookie_cleared(response) -> bool:
            set_cookies = response.headers.get_list("set-cookie")
            return any(
                "pmis_oidc_bind=" in c
                and ("Max-Age=0" in c or "max-age=0" in c or "expires=" in c.lower())
                for c in set_cookies
            )

        # Helper to check if pmis_oidc_bind cookie was set/cleared at all in response
        def has_binding_cookie_header(response) -> bool:
            set_cookies = response.headers.get_list("set-cookie")
            return any("pmis_oidc_bind=" in c for c in set_cookies)

        # 1. Downstream token exchange failure: cookie must be cleared
        state_fail_exchange = "state-fail-exchange"
        with SessionLocal() as db:
            db.add(
                OIDCState(
                    state=state_fail_exchange,
                    nonce="nonce-fail-exchange",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                    code_verifier="verifier-fail-exchange",
                    binding_digest=digest,
                )
            )
            db.commit()

        mock_client.exchange_code.side_effect = HTTPException(
            status_code=502, detail="OIDC provider connection failed or timed out"
        )
        client = TestClient(app, base_url="https://testserver")
        client.cookies.set("pmis_oidc_bind", raw_cookie)
        resp = client.get(
            f"/api/v1/auth/callback?code=fail-code&state={state_fail_exchange}",
            follow_redirects=False,
        )
        assert resp.status_code == 502
        assert is_binding_cookie_cleared(resp)

        # 2. Downstream inactive user failure: cookie must be cleared
        state_inactive = "state-inactive-user"
        nonce_inactive = "nonce-inactive-user"
        with SessionLocal() as db:
            db.add(
                OIDCState(
                    state=state_inactive,
                    nonce=nonce_inactive,
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                    code_verifier="verifier-inactive",
                    binding_digest=digest,
                )
            )
            # Create inactive user in db
            db.add(
                User(
                    sub="sub-inactive-user",
                    email="inactive@example.com",
                    name="Inactive User",
                    is_active=False,
                )
            )
            db.commit()

        token_inactive = make_signed_token(
            {
                "iss": "https://idp.example.com",
                "aud": "pmis-app",
                "sub": "sub-inactive-user",
                "nonce": nonce_inactive,
                "exp": time.time() + 3600,
                "email": "inactive@example.com",
                "name": "Inactive User",
            },
            app.state.priv_key,
        )
        mock_client.exchange_code.side_effect = None
        mock_client.exchange_code.return_value = {
            "access_token": "mock-access",
            "id_token": token_inactive,
            "token_type": "Bearer",
        }
        resp_inactive = client.get(
            f"/api/v1/auth/callback?code=inactive-code&state={state_inactive}",
            follow_redirects=False,
        )
        assert resp_inactive.status_code == 403
        assert is_binding_cookie_cleared(resp_inactive)

        # 3. Pre-consumption failure: mismatched binding cookie
        # Cookie must NOT be cleared (retained for Browser A)
        state_pre_reject = "state-pre-reject"
        with SessionLocal() as db:
            db.add(
                OIDCState(
                    state=state_pre_reject,
                    nonce="nonce-pre-reject",
                    redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
                    created_at=time.time(),
                    expires_at=time.time() + 600,
                    code_verifier="verifier-pre-reject",
                    binding_digest=digest,
                )
            )
            db.commit()

        client_mismatch = TestClient(app, base_url="https://testserver")
        client_mismatch.cookies.set("pmis_oidc_bind", "wrong-token-for-another-browser")
        resp_mismatch = client_mismatch.get(
            f"/api/v1/auth/callback?code=mismatch-code&state={state_pre_reject}",
            follow_redirects=False,
        )
        assert resp_mismatch.status_code == 400
        assert not has_binding_cookie_header(resp_mismatch)
        # Transaction is still intact in DB
        with SessionLocal() as db:
            assert db.query(OIDCState).filter_by(state=state_pre_reject).first() is not None

        # 4. Pre-consumption failure: unknown state
        # Cookie must NOT be cleared
        resp_unknown = client_mismatch.get(
            "/api/v1/auth/callback?code=unknown-code&state=nonexistent-state",
            follow_redirects=False,
        )
        assert resp_unknown.status_code == 400
        assert not has_binding_cookie_header(resp_unknown)
    finally:
        engine.dispose()


def test_default_oidc_client_token_request_body_carries_code_verifier():
    settings = Settings(
        database_url=None,
        oidc_issuer="https://idp.example.com",
        oidc_client_id="pmis-app",
        oidc_client_secret=SecretStr("super-secret-client-key"),
        oidc_authorization_endpoint="https://idp.example.com/auth",
        oidc_token_endpoint="https://idp.example.com/token",
        oidc_jwks_uri="https://idp.example.com/jwks",
        oidc_redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
    )
    client = DefaultOIDCClient(settings)
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(
        {
            "access_token": "mock-token",
            "id_token": "mock-id-token",
            "token_type": "Bearer",
        }
    ).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = client.exchange_code(
            code="auth-code-123",
            redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
            code_verifier="test-pkce-verifier-98765432101234567890",
        )
        assert result["id_token"] == "mock-id-token"
        assert mock_urlopen.call_count == 1
        req = mock_urlopen.call_args[0][0]
        assert isinstance(req, urllib.request.Request)
        assert req.get_method() == "POST"
        assert req.full_url == "https://idp.example.com/token"
        assert req.headers.get("Content-type") == "application/x-www-form-urlencoded"

        assert isinstance(req.data, bytes)
        body_params = urllib.parse.parse_qs(req.data.decode("utf-8"))
        assert body_params["grant_type"] == ["authorization_code"]
        assert body_params["code"] == ["auth-code-123"]
        assert body_params["redirect_uri"] == ["http://127.0.0.1:8000/api/v1/auth/callback"]
        assert body_params["client_id"] == ["pmis-app"]
        assert body_params["client_secret"] == ["super-secret-client-key"]
        assert body_params["code_verifier"] == ["test-pkce-verifier-98765432101234567890"]
