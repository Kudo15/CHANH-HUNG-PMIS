import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sub: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        foreign_keys="UserRole.user_id",
        cascade="all, delete-orphan",
        back_populates="user",
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", cascade="all, delete-orphan", back_populates="user"
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    granted_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    second_admin_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    bootstrap_receipt_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("admin_bootstrap_receipts.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="roles")
    bootstrap_receipt: Mapped["AdminBootstrapReceipt | None"] = relationship(
        "AdminBootstrapReceipt", foreign_keys=[bootstrap_receipt_id]
    )


class AdminBootstrapReceipt(Base):
    __tablename__ = "admin_bootstrap_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    environment: Mapped[str] = mapped_column(String(50), nullable=False)
    target_user1_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    target_user2_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    target_sub1: Mapped[str] = mapped_column(String(255), nullable=False)
    target_sub2: Mapped[str] = mapped_column(String(255), nullable=False)
    approver1_role: Mapped[str] = mapped_column(String(50), nullable=False)
    approver1_key_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    approver2_role: Mapped[str] = mapped_column(String(50), nullable=False)
    approver2_key_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    consumed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    single_bootstrap_lock: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, default="BOOTSTRAP_LOCK"
    )

    target_user1: Mapped["User"] = relationship("User", foreign_keys=[target_user1_id])
    target_user2: Mapped["User"] = relationship("User", foreign_keys=[target_user2_id])


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")


class OIDCState(Base):
    __tablename__ = "oidc_states"

    state: Mapped[str] = mapped_column(String(64), primary_key=True)
    nonce: Mapped[str] = mapped_column(String(64), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)
    expires_at: Mapped[float] = mapped_column(Float, nullable=False)


class SystemAdminRequest(Base):
    __tablename__ = "system_admin_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    requester_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    approver_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    target_user: Mapped["User"] = relationship("User", foreign_keys=[target_user_id])
    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_id])
    approver: Mapped["User | None"] = relationship("User", foreign_keys=[approver_id])
