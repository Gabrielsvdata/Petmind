"""Add reset token fields to usuarios

Revision ID: c9f9e6a4b201
Revises: a66159c11155
Create Date: 2026-07-15 00:00:01.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9f9e6a4b201"
down_revision: str | Sequence[str] | None = "a66159c11155"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "usuarios",
        sa.Column("reset_token", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column("reset_token_expires_at", sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_usuarios_reset_token", "usuarios", ["reset_token"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_usuarios_reset_token", "usuarios", type_="unique")
    op.drop_column("usuarios", "reset_token_expires_at")
    op.drop_column("usuarios", "reset_token")
