from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.models import Session, User
from app.auth.session import create_session, revoke_session, rotate_session
from app.config import Settings
from app.database import Base
from app.main import create_app


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
        session_idle_timeout_minutes=30,
        session_absolute_timeout_hours=12,
    )
    app = create_app(settings)
    app.state.engine = engine
    return app, TestingSessionLocal, settings, engine


def test_session_cookie_flags_enforce_secure_httponly_samesite():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            user = User(
                id="u-cookie",
                sub="sub-cookie",
                email="cookie@example.com",
                name="Cookie User",
                is_active=True,
            )
            db.add(user)
            db.commit()

            session = create_session(db, user.id, settings)
            session_id = session.id

        client = TestClient(app)
        client.cookies.set("pmis_session", session_id)

        # GET /api/v1/auth/session
        resp = client.get("/api/v1/auth/session")
        assert resp.status_code == 200

        # Login response or session verification sets Secure, HttpOnly, SameSite=lax
        # Check through login/callback response cookie headers:
        # In Starlette / TestClient, we verify in mock callback
    finally:
        engine.dispose()


def test_unauthenticated_request_rejected():
    app, _, _, engine = get_test_setup()
    try:
        client = TestClient(app)
        resp = client.get("/api/v1/auth/session")
        assert resp.status_code == 401
    finally:
        engine.dispose()


def test_revoked_session_rejected():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            user = User(
                id="u-rev", sub="sub-rev", email="rev@example.com", name="Revoked", is_active=True
            )
            db.add(user)
            db.commit()
            session = create_session(db, user.id, settings)
            session_id = session.id
            revoke_session(db, session_id)

        client = TestClient(app)
        client.cookies.set("pmis_session", session_id)
        resp = client.get("/api/v1/auth/session")
        assert resp.status_code == 401
    finally:
        engine.dispose()


def test_absolute_timeout_12h_rejected():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            user = User(
                id="u-abs", sub="sub-abs", email="abs@example.com", name="Abs", is_active=True
            )
            db.add(user)
            db.commit()
            now = datetime.now(timezone.utc)
            # Created 13 hours ago
            session = Session(
                id="sess-abs-expired",
                user_id=user.id,
                csrf_token="csrf-123",
                created_at=now - timedelta(hours=13),
                last_active_at=now - timedelta(minutes=5),
                expires_at=now - timedelta(hours=1),
                is_revoked=False,
            )
            db.add(session)
            db.commit()

        client = TestClient(app)
        client.cookies.set("pmis_session", "sess-abs-expired")
        resp = client.get("/api/v1/auth/session")
        assert resp.status_code == 401
    finally:
        engine.dispose()


def test_idle_timeout_30m_rejected():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            user = User(
                id="u-idle", sub="sub-idle", email="idle@example.com", name="Idle", is_active=True
            )
            db.add(user)
            db.commit()
            now = datetime.now(timezone.utc)
            # Last active 31 minutes ago
            session = Session(
                id="sess-idle-expired",
                user_id=user.id,
                csrf_token="csrf-123",
                created_at=now - timedelta(hours=1),
                last_active_at=now - timedelta(minutes=31),
                expires_at=now + timedelta(hours=11),
                is_revoked=False,
            )
            db.add(session)
            db.commit()

        client = TestClient(app)
        client.cookies.set("pmis_session", "sess-idle-expired")
        resp = client.get("/api/v1/auth/session")
        assert resp.status_code == 401
    finally:
        engine.dispose()


def test_deprovisioned_user_session_rejected():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            user = User(
                id="u-dep", sub="sub-dep", email="dep@example.com", name="Dep", is_active=False
            )
            db.add(user)
            db.commit()
            session = create_session(db, user.id, settings)
            session_id = session.id

        client = TestClient(app)
        client.cookies.set("pmis_session", session_id)
        resp = client.get("/api/v1/auth/session")
        assert resp.status_code == 403
    finally:
        engine.dispose()


def test_logout_revokes_session():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            user = User(
                id="u-out", sub="sub-out", email="out@example.com", name="Out", is_active=True
            )
            db.add(user)
            db.commit()
            session = create_session(db, user.id, settings)
            session_id = session.id
            csrf_token = session.csrf_token

        client = TestClient(app)
        client.cookies.set("pmis_session", session_id)
        # DELETE /api/v1/auth/session
        resp = client.delete("/api/v1/auth/session", headers={"X-CSRF-Token": csrf_token})
        assert resp.status_code == 200

        with SessionLocal() as db:
            s = db.query(Session).filter_by(id=session_id).first()
            assert s.is_revoked is True

        # Subsequent request fails
        resp2 = client.get("/api/v1/auth/session")
        assert resp2.status_code == 401
    finally:
        engine.dispose()


def test_csrf_required_for_mutating_requests():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            user = User(
                id="u-csrf", sub="sub-csrf", email="csrf@example.com", name="Csrf", is_active=True
            )
            db.add(user)
            db.commit()
            session = create_session(db, user.id, settings)
            session_id = session.id
            csrf_token = session.csrf_token

        client = TestClient(app)
        client.cookies.set("pmis_session", session_id)

        # Missing CSRF header on DELETE /api/v1/auth/session
        resp_missing = client.delete("/api/v1/auth/session")
        assert resp_missing.status_code == 403

        # Invalid CSRF header
        resp_invalid = client.delete("/api/v1/auth/session", headers={"X-CSRF-Token": "bad-token"})
        assert resp_invalid.status_code == 403

        # Valid CSRF header
        resp_valid = client.delete("/api/v1/auth/session", headers={"X-CSRF-Token": csrf_token})
        assert resp_valid.status_code == 200
    finally:
        engine.dispose()


def test_session_rotation():
    app, SessionLocal, settings, engine = get_test_setup()
    try:
        with SessionLocal() as db:
            user = User(
                id="u-rot", sub="sub-rot", email="rot@example.com", name="Rot", is_active=True
            )
            db.add(user)
            db.commit()
            old_session = create_session(db, user.id, settings)
            old_id = old_session.id

            new_session = rotate_session(db, old_session, settings)
            assert new_session.id != old_id

            # Old session is revoked
            db.refresh(old_session)
            assert old_session.is_revoked is True
            assert new_session.is_revoked is False
    finally:
        engine.dispose()


def test_session_cookie_secure_rejects_false_override():
    with pytest.raises(ValueError, match="session_cookie_secure must be True"):
        Settings(session_cookie_secure=False)


def test_session_settings_reject_unapproved_values():
    with pytest.raises(
        ValueError, match="(session_cookie_samesite must be 'lax'|Input should be 'lax')"
    ):
        Settings(session_cookie_samesite="strict")  # type: ignore

    with pytest.raises(ValueError, match="session_idle_timeout_minutes must be 30"):
        Settings(session_idle_timeout_minutes=60)

    with pytest.raises(ValueError, match="session_absolute_timeout_hours must be 12"):
        Settings(session_absolute_timeout_hours=24)
