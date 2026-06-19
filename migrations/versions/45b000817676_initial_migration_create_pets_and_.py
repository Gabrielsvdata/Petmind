"""Initial migration: create pets and registros_comportamento tables

Revision ID: 45b000817676
Revises:
Create Date: 2026-06-19 19:57:49.718596

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '45b000817676'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "pets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("raca", sa.String(length=100), nullable=False),
        sa.Column(
            "especie",
            sa.String(length=20),
            nullable=False,
            server_default="cachorro",
        ),
        sa.Column("idade", sa.Integer(), nullable=False),
        sa.Column("peso", sa.Float(), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_pets_id", "id"),
    )
    op.create_table(
        "registros_comportamento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pet_id", sa.Integer(), nullable=False),
        sa.Column("data_hora", sa.DateTime(), nullable=False),
        sa.Column("agitacao", sa.Integer(), nullable=False),
        sa.Column("sono", sa.Integer(), nullable=False),
        sa.Column("apetite", sa.Integer(), nullable=False),
        sa.Column("humor", sa.Integer(), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["pet_id"],
            ["pets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_registros_comportamento_id", "id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('registros_comportamento')
    op.drop_table('pets')
