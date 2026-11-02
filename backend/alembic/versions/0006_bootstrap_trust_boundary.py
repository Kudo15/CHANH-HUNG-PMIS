"""Add bootstrap instance state, receipt metadata, and receipt immutability.

Revision ID: 0006_bootstrap_trust_boundary
Revises: 0005_initial_admin_bootstrap
Create Date: 2026-10-31
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0006_bootstrap_trust_boundary"
down_revision: Union[str, None] = "0005_initial_admin_bootstrap"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create admin_bootstrap_instance_state table
    op.create_table(
        "admin_bootstrap_instance_state",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("instance_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "singleton_lock",
            sa.String(length=20),
            nullable=False,
            server_default="INSTANCE_LOCK",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_id"),
        sa.UniqueConstraint("singleton_lock"),
    )

    # 2. Add W9 audit and boundary columns to admin_bootstrap_receipts
    with op.batch_alter_table("admin_bootstrap_receipts") as batch_op:
        batch_op.add_column(sa.Column("instance_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("request_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("operator_id", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))

    # 3. DB-level update/delete immutability protection for admin_bootstrap_receipts
    bind = op.get_bind()
    dialect_name = bind.dialect.name if bind else "postgresql"

    if dialect_name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION prevent_admin_bootstrap_receipt_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'admin_bootstrap_receipts rows are immutable';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_protect_admin_bootstrap_receipts
            BEFORE UPDATE OR DELETE ON admin_bootstrap_receipts
            FOR EACH ROW EXECUTE FUNCTION prevent_admin_bootstrap_receipt_mutation();
            """
        )
    elif dialect_name == "sqlite":
        op.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_protect_admin_bootstrap_receipts_update
            BEFORE UPDATE ON admin_bootstrap_receipts
            BEGIN
                SELECT RAISE(ABORT, 'admin_bootstrap_receipts rows are immutable');
            END;
            """
        )
        op.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_protect_admin_bootstrap_receipts_delete
            BEFORE DELETE ON admin_bootstrap_receipts
            BEGIN
                SELECT RAISE(ABORT, 'admin_bootstrap_receipts rows are immutable');
            END;
            """
        )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade of 0006_bootstrap_trust_boundary is refused to preserve "
        "bootstrap receipt audit trail and instance state immutability."
    )
