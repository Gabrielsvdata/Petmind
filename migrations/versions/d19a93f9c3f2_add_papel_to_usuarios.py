"""Add papel to usuarios

Revision ID: d19a93f9c3f2
Revises: c9f9e6a4b201
Create Date: 2026-07-15 00:00:02.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d19a93f9c3f2"
down_revision: str | Sequence[str] | None = "c9f9e6a4b201"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "usuarios",
        sa.Column(
            "papel",
            sa.String(length=20),
            nullable=False,
            server_default="usuario",
        ),
    )
    op.alter_column("usuarios", "papel", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("usuarios", "papel")
