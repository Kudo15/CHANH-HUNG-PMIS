"""Add PKCE code verifier and browser binding digest to oidc_states.

Revision ID: 0007_oidc_pkce_browser_binding
Revises: 0006_bootstrap_trust_boundary
Create Date: 2026-11-02
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0007_oidc_pkce_browser_binding"
down_revision: Union[str, None] = "0006_bootstrap_trust_boundary"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("oidc_states") as batch_op:
        batch_op.add_column(sa.Column("code_verifier", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("binding_digest", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("oidc_states") as batch_op:
        batch_op.drop_column("binding_digest")
        batch_op.drop_column("code_verifier")
