"""Create initial admin bootstrap receipt table and update user roles.

Revision ID: 0005_initial_admin_bootstrap
Revises: 0004_projects_tasks_audit
Create Date: 2026-10-31
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0005_initial_admin_bootstrap"
down_revision: Union[str, None] = "0004_projects_tasks_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create admin_bootstrap_receipts table
    op.create_table(
        "admin_bootstrap_receipts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("environment", sa.String(length=50), nullable=False),
        sa.Column("target_user1_id", sa.String(length=36), nullable=False),
        sa.Column("target_user2_id", sa.String(length=36), nullable=False),
        sa.Column("target_sub1", sa.String(length=255), nullable=False),
        sa.Column("target_sub2", sa.String(length=255), nullable=False),
        sa.Column("approver1_role", sa.String(length=50), nullable=False),
        sa.Column("approver1_key_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("approver2_role", sa.String(length=50), nullable=False),
        sa.Column("approver2_key_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("payload_digest", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "single_bootstrap_lock",
            sa.String(length=20),
            nullable=False,
            server_default="BOOTSTRAP_LOCK",
        ),
        sa.ForeignKeyConstraint(["target_user1_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_user2_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("single_bootstrap_lock"),
    )

    # 2. Update user_roles: make granted_by nullable, add bootstrap_receipt_id
    with op.batch_alter_table("user_roles") as batch_op:
        batch_op.alter_column(
            "granted_by",
            existing_type=sa.String(length=36),
            nullable=True,
        )
        batch_op.add_column(sa.Column("bootstrap_receipt_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_user_roles_bootstrap_receipt_id",
            "admin_bootstrap_receipts",
            ["bootstrap_receipt_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("user_roles") as batch_op:
        batch_op.drop_constraint("fk_user_roles_bootstrap_receipt_id", type_="foreignkey")
        batch_op.drop_column("bootstrap_receipt_id")
        batch_op.alter_column(
            "granted_by",
            existing_type=sa.String(length=36),
            nullable=False,
        )

    op.drop_table("admin_bootstrap_receipts")
