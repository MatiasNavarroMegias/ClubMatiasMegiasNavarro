"""create reservation reminders table

Revision ID: 8d4e5f6a7b8c
Revises: 19f60949f2d2
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8d4e5f6a7b8c"
down_revision: str | Sequence[str] | None = "19f60949f2d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reservation_reminders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reservation_id", sa.Integer(), nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_reservation_reminders_reservation_id"),
        "reservation_reminders",
        ["reservation_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_reservation_reminders_reservation_id"),
        table_name="reservation_reminders",
    )
    op.drop_table("reservation_reminders")
