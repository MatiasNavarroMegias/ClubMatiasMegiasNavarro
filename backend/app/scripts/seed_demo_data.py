from dataclasses import dataclass
from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.normalization import build_sports_space_code
from app.models import SportsSpace, Venue

DEMO_VENUE_NAME = "Sede Moron"
DEMO_VENUE_ADDRESS = "Rivadavia 19850"
DEMO_OPENING_TIME = time(8, 0)
DEMO_CLOSING_TIME = time(23, 0)

DEMO_SPACES = (
    ("Cancha de Futbol 1", "Futbol", 1),
    ("Cancha de Futbol 2", "Futbol", 2),
    ("Cancha de Paddle 1", "Paddle", 1),
)


@dataclass(frozen=True)
class SeedResult:
    venues_created: int
    spaces_created: int


def seed_demo_data(database_session: Session) -> SeedResult:
    """
    Carga datos publicos de demostracion sin tocar datos de usuarios.

    La sede se identifica por su nombre exacto. Los espacios se identifican
    primero por composite_code y luego por sede, tipo y numero. La funcion
    confirma una unica transaccion y revierte todos los cambios si ocurre
    cualquier error.
    """
    venues_created = 0
    spaces_created = 0

    try:
        venue = database_session.scalar(
            select(Venue).where(Venue.name == DEMO_VENUE_NAME),
        )

        if venue is None:
            venue = Venue(
                name=DEMO_VENUE_NAME,
                address=DEMO_VENUE_ADDRESS,
                opening_time=DEMO_OPENING_TIME,
                closing_time=DEMO_CLOSING_TIME,
                is_active=True,
            )
            database_session.add(venue)
            database_session.flush()
            venues_created = 1

        for name, sport_type, space_number in DEMO_SPACES:
            composite_code = build_sports_space_code(
                venue_name=venue.name,
                venue_address=venue.address,
                sport_type=sport_type,
                space_number=space_number,
            )
            existing_space = database_session.scalar(
                select(SportsSpace).where(
                    SportsSpace.composite_code == composite_code,
                ),
            )

            if existing_space is None:
                existing_space = database_session.scalar(
                    select(SportsSpace).where(
                        SportsSpace.venue_id == venue.id,
                        SportsSpace.sport_type == sport_type,
                        SportsSpace.space_number == space_number,
                    ),
                )

            if existing_space is not None:
                continue

            database_session.add(
                SportsSpace(
                    venue_id=venue.id,
                    name=name,
                    sport_type=sport_type,
                    space_number=space_number,
                    composite_code=composite_code,
                    is_active=True,
                )
            )
            spaces_created += 1

        database_session.commit()
    except Exception:
        database_session.rollback()
        raise

    return SeedResult(
        venues_created=venues_created,
        spaces_created=spaces_created,
    )


def main() -> None:
    database_session = SessionLocal()

    try:
        result = seed_demo_data(database_session)
    finally:
        database_session.close()

    print(f"sedes creadas: {result.venues_created}")
    print(f"espacios creados: {result.spaces_created}")


if __name__ == "__main__":
    main()
