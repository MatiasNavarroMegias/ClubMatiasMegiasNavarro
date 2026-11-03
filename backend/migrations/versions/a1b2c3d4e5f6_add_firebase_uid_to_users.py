"""add Firebase Authentication identity to users

Revision ID: a1b2c3d4e5f6
Revises: 91c2d4e5f6a7
Create Date: 2026-11-03 18:40:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "91c2d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Agrega la identidad Firebase sin modificar usuarios existentes."""
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=True,
    )
    op.add_column(
        "users",
        sa.Column("firebase_uid", sa.String(length=128), nullable=True),
    )
    op.create_index(
        op.f("ix_users_firebase_uid"),
        "users",
        ["firebase_uid"],
        unique=True,
    )


def downgrade() -> None:
    """Revierte la identidad Firebase solo si no existen perfiles Firebase."""
    op.drop_index(op.f("ix_users_firebase_uid"), table_name="users")
    op.drop_column("users", "firebase_uid")
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
    )
