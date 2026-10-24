"""create sports spaces table

Revision ID: 003a7c1c837a
Revises: 9b379a5e7cc7
Create Date: 2026-10-24 13:30:10.596513

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003a7c1c837a"
down_revision: str | Sequence[str] | None = "9b379a5e7cc7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Crea la tabla sports_spaces y sus indices.

    Cada espacio pertenece obligatoriamente a una sede. La combinacion
    de sede, deporte y numero identifica de forma unica un espacio
    deportivo dentro del club.
    """
    op.create_table(
        "sports_spaces",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "venue_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "sport_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "space_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
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
            "space_number > 0",
            name="ck_sports_spaces_space_number_positive",
        ),
        sa.ForeignKeyConstraint(
            ["venue_id"],
            ["venues.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "venue_id",
            "sport_type",
            "space_number",
            name="uq_sports_spaces_venue_sport_number",
        ),
    )

    op.create_index(
        op.f("ix_sports_spaces_sport_type"),
        "sports_spaces",
        ["sport_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sports_spaces_venue_id"),
        "sports_spaces",
        ["venue_id"],
        unique=False,
    )


def downgrade() -> None:
    """
    Elimina los indices y la tabla sports_spaces.

    Los indices se eliminan antes de la tabla para revertir
    completamente la estructura creada por upgrade.
    """
    op.drop_index(
        op.f("ix_sports_spaces_venue_id"),
        table_name="sports_spaces",
    )
    op.drop_index(
        op.f("ix_sports_spaces_sport_type"),
        table_name="sports_spaces",
    )
    op.drop_table("sports_spaces")
