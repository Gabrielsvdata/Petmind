"""Remove reset token fields from usuarios

Revision ID: f4d2b6e8a1c3
Revises: d19a93f9c3f2
Create Date: 2026-07-15 00:00:03.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4d2b6e8a1c3"
down_revision: str | Sequence[str] | None = "d19a93f9c3f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("uq_usuarios_reset_token", "usuarios", type_="unique")
    op.drop_column("usuarios", "reset_token_expires_at")
    op.drop_column("usuarios", "reset_token")


def downgrade() -> None:
    """Downgrade schema."""
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
