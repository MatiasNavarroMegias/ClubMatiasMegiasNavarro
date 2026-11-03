from dataclasses import dataclass
from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.normalization import build_sports_space_code
from app.models import SportsSpace, Venue


@dataclass(frozen=True)
class DemoVenue:
    name: str
    address: str
    opening_time: time
    closing_time: time
    sport_types: tuple[str, ...]


DEMO_VENUES = (
    DemoVenue(
        name="Sede Moron",
        address="Rivadavia 19850",
        opening_time=time(8, 0),
        closing_time=time(23, 0),
        sport_types=("Futbol", "Paddle", "Basquet"),
    ),
    DemoVenue(
        name="Sede Ramos Mejia",
        address="Avenida de Mayo 1200",
        opening_time=time(8, 0),
        closing_time=time(23, 0),
        sport_types=("Futbol", "Tenis", "Voley"),
    ),
    DemoVenue(
        name="Sede Haedo",
        address="Rivadavia 16200",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        sport_types=("Futbol", "Paddle", "Hockey"),
    ),
    DemoVenue(
        name="Sede Castelar",
        address="Arias 2500",
        opening_time=time(8, 0),
        closing_time=time(22, 0),
        sport_types=("Futbol", "Tenis", "Basquet"),
    ),
)


@dataclass(frozen=True)
class SeedResult:
    venues_created: int
    spaces_created: int


def seed_demo_data(database_session: Session) -> SeedResult:
    """
    Carga datos publicos de demostracion sin tocar datos de usuarios.

    Las sedes se identifican por su nombre exacto. Los espacios se
    identifican primero por composite_code y luego por sede, tipo y numero.
    La funcion confirma una unica transaccion y revierte todos los cambios
    si ocurre cualquier error.
    """
    venues_created = 0
    spaces_created = 0

    try:
        for demo_venue in DEMO_VENUES:
            venue = database_session.scalar(
                select(Venue).where(Venue.name == demo_venue.name),
            )

            if venue is None:
                venue = Venue(
                    name=demo_venue.name,
                    address=demo_venue.address,
                    opening_time=demo_venue.opening_time,
                    closing_time=demo_venue.closing_time,
                    is_active=True,
                )
                database_session.add(venue)
                database_session.flush()
                venues_created += 1

            for sport_type in demo_venue.sport_types:
                for space_number in (1, 2):
                    name = f"Cancha de {sport_type} {space_number}"
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
