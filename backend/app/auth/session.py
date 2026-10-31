import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession

from app.auth.models import Session as SessionModel
from app.auth.models import User, UserRole
from app.config import Settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def create_session(db: DBSession, user_id: str, settings: Settings) -> SessionModel:
    now = utc_now()
    session_id = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    expires_at = now + timedelta(hours=settings.session_absolute_timeout_hours)

    session = SessionModel(
        id=session_id,
        user_id=user_id,
        csrf_token=csrf_token,
        created_at=now,
        last_active_at=now,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def validate_session(
    db: DBSession, session_id: str, settings: Settings
) -> tuple[SessionModel, User, list[str]]:
    session = db.query(SessionModel).filter_by(id=session_id).first()
    if not session or session.is_revoked:
        raise HTTPException(status_code=401, detail="Session invalid or revoked")

    now = utc_now()

    # 1. Absolute timeout
    if now >= ensure_utc(session.expires_at):
        session.is_revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired (absolute timeout)")

    # 2. Idle timeout
    idle_limit = timedelta(minutes=settings.session_idle_timeout_minutes)
    if now - ensure_utc(session.last_active_at) > idle_limit:
        session.is_revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired (idle timeout)")

    # 3. Check user state
    user = db.query(User).filter_by(id=session.user_id).first()
    if not user:
        session.is_revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        session.is_revoked = True
        db.commit()
        raise HTTPException(status_code=403, detail="User account is inactive or deprovisioned")

    # Update last_active_at (slide window)
    session.last_active_at = now
    db.commit()
    db.refresh(session)

    roles = [r.role for r in db.query(UserRole).filter_by(user_id=user.id).all()]
    return session, user, roles


def rotate_session(db: DBSession, old_session: SessionModel, settings: Settings) -> SessionModel:
    old_session.is_revoked = True
    db.commit()
    return create_session(db, old_session.user_id, settings)


def revoke_session(db: DBSession, session_id: str) -> None:
    session = db.query(SessionModel).filter_by(id=session_id).first()
    if session:
        session.is_revoked = True
        db.commit()


def revoke_user_sessions(db: DBSession, user_id: str) -> None:
    sessions = db.query(SessionModel).filter_by(user_id=user_id, is_revoked=False).all()
    for s in sessions:
        s.is_revoked = True
    db.commit()


def validate_csrf(session: SessionModel, csrf_header: str | None) -> None:
    if not csrf_header or not secrets.compare_digest(csrf_header, session.csrf_token):
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")
