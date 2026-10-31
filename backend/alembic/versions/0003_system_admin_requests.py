"""Create system admin dual-control request table.

Revision ID: 0003_system_admin_requests
Revises: 0002_auth_foundation
Create Date: 2026-10-30
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0003_system_admin_requests"
down_revision: Union[str, None] = "0002_auth_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_admin_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("target_user_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("requester_id", sa.String(length=36), nullable=False),
        sa.Column("approver_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_system_admin_requests_target_user_id"),
        "system_admin_requests",
        ["target_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_system_admin_requests_target_user_id"),
        table_name="system_admin_requests",
    )
    op.drop_table("system_admin_requests")
