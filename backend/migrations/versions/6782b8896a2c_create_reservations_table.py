"""create reservations table

Revision ID: 6782b8896a2c
Revises: 003a7c1c837a
Create Date: 2026-10-27 11:58:26.494877

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6782b8896a2c"
down_revision: str | Sequence[str] | None = "003a7c1c837a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Crea la tabla reservations y sus indices.

    Cada reserva pertenece obligatoriamente a un usuario y a un
    espacio deportivo. Las restricciones conservan la coherencia
    temporal, el estado y la cancelacion del registro.
    """
    op.create_table(
        "reservations",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "sports_space_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "start_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "end_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="confirmed",
            nullable=False,
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "end_at > start_at",
            name="ck_reservations_end_after_start",
        ),
        sa.CheckConstraint(
            "status IN ('confirmed', 'cancelled')",
            name="ck_reservations_valid_status",
        ),
        sa.CheckConstraint(
            (
                "(status = 'confirmed' AND cancelled_at IS NULL) OR "
                "(status = 'cancelled' AND cancelled_at IS NOT NULL)"
            ),
            name="ck_reservations_cancellation_consistency",
        ),
        sa.ForeignKeyConstraint(
            ["sports_space_id"],
            ["sports_spaces.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_reservations_sports_space_id"),
        "reservations",
        ["sports_space_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reservations_start_at"),
        "reservations",
        ["start_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reservations_status"),
        "reservations",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reservations_user_id"),
        "reservations",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """
    Elimina los indices y la tabla reservations.

    Los indices se eliminan antes de la tabla para revertir
    completamente la estructura creada durante upgrade.
    """
    op.drop_index(
        op.f("ix_reservations_user_id"),
        table_name="reservations",
    )
    op.drop_index(
        op.f("ix_reservations_status"),
        table_name="reservations",
    )
    op.drop_index(
        op.f("ix_reservations_start_at"),
        table_name="reservations",
    )
    op.drop_index(
        op.f("ix_reservations_sports_space_id"),
        table_name="reservations",
    )
    op.drop_table("reservations")
