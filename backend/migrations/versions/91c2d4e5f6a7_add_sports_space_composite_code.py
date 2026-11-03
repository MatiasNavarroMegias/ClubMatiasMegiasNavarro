"""add sports space composite code

Revision ID: 91c2d4e5f6a7
Revises: 8d4e5f6a7b8c
"""

import re
import unicodedata
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "91c2d4e5f6a7"
down_revision: str | Sequence[str] | None = "8d4e5f6a7b8c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _normalize(value: str) -> str:
    without_accents = "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^A-Za-z0-9]+", "_", without_accents).strip("_")


def upgrade() -> None:
    op.add_column(
        "sports_spaces",
        sa.Column("composite_code", sa.String(length=255), nullable=True),
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT sports_spaces.id, venues.name, venues.address,
                   sports_spaces.sport_type, sports_spaces.space_number
            FROM sports_spaces
            JOIN venues ON venues.id = sports_spaces.venue_id
            """
        )
    ).mappings()

    for row in rows:
        components = (
            row["name"],
            row["address"],
            row["sport_type"],
            str(row["space_number"]),
        )
        composite_code = "_".join(_normalize(component) for component in components)
        connection.execute(
            sa.text(
                "UPDATE sports_spaces SET composite_code = :composite_code "
                "WHERE id = :sports_space_id"
            ),
            {
                "composite_code": composite_code,
                "sports_space_id": row["id"],
            },
        )

    op.alter_column("sports_spaces", "composite_code", nullable=False)
    op.create_unique_constraint(
        "uq_sports_spaces_composite_code",
        "sports_spaces",
        ["composite_code"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_sports_spaces_composite_code",
        "sports_spaces",
        type_="unique",
    )
    op.drop_column("sports_spaces", "composite_code")
