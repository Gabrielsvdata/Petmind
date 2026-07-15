"""Create usuarios table and owner_id relation

Revision ID: a66159c11155
Revises: 45b000817676
Create Date: 2026-07-15 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a66159c11155"
down_revision: str | Sequence[str] | None = "45b000817676"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_usuarios_id", "usuarios", ["id"], unique=False)
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=False)
    op.add_column("pets", sa.Column("owner_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_pets_owner_id_usuarios", "pets", "usuarios", ["owner_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_pets_owner_id_usuarios", "pets", type_="foreignkey")
    op.drop_column("pets", "owner_id")
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_index("ix_usuarios_id", table_name="usuarios")
    op.drop_table("usuarios")
