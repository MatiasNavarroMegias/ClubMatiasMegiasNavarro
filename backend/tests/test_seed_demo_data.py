from datetime import time

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.normalization import build_sports_space_code
from app.models import (
    PushDevice,
    Reservation,
    ReservationReminder,
    SportsSpace,
    User,
    Venue,
)
from app.scripts.seed_demo_data import seed_demo_data


def create_database_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_seed_creates_four_venues_and_24_spaces() -> None:
    session = create_database_session()

    result = seed_demo_data(session)

    assert result.venues_created == 4
    assert result.spaces_created == 24
    assert session.scalar(select(func.count()).select_from(Venue)) == 4
    assert session.scalar(select(func.count()).select_from(SportsSpace)) == 24
    session.close()


def test_seed_is_idempotent_and_does_not_duplicate_data() -> None:
    session = create_database_session()

    first_result = seed_demo_data(session)
    second_result = seed_demo_data(session)

    assert first_result.venues_created == 4
    assert first_result.spaces_created == 24
    assert second_result.venues_created == 0
    assert second_result.spaces_created == 0
    assert session.scalar(select(func.count()).select_from(Venue)) == 4
    assert session.scalar(select(func.count()).select_from(SportsSpace)) == 24
    session.close()


def test_each_venue_has_three_sports_and_two_spaces_per_sport() -> None:
    session = create_database_session()
    seed_demo_data(session)

    venues = session.scalars(select(Venue).order_by(Venue.name)).all()

    for venue in venues:
        spaces = session.scalars(
            select(SportsSpace).where(SportsSpace.venue_id == venue.id),
        ).all()
        spaces_by_sport = {}
        for space in spaces:
            spaces_by_sport.setdefault(space.sport_type, []).append(space)

        assert len(spaces_by_sport) == 3
        assert len(spaces) == 6
        assert {len(sport_spaces) for sport_spaces in spaces_by_sport.values()} == {2}
        assert all(space.is_active for space in spaces)

    session.close()


def test_composite_codes_are_unique_and_domain_generated() -> None:
    session = create_database_session()
    seed_demo_data(session)

    spaces = session.scalars(select(SportsSpace)).all()
    codes = [space.composite_code for space in spaces]

    assert all(codes)
    assert len(codes) == len(set(codes)) == 24
    for space in spaces:
        venue = session.get(Venue, space.venue_id)
        assert venue is not None
        assert space.composite_code == build_sports_space_code(
            venue_name=venue.name,
            venue_address=venue.address,
            sport_type=space.sport_type,
            space_number=space.space_number,
        )

    session.close()


def test_seed_creates_only_missing_spaces_for_existing_venue() -> None:
    session = create_database_session()
    venue = Venue(
        name="Sede Moron",
        address="Rivadavia 19850",
        opening_time=time(8, 0),
        closing_time=time(23, 0),
        is_active=True,
    )
    session.add(venue)
    session.flush()
    session.add(
        SportsSpace(
            venue_id=venue.id,
            name="Cancha de Futbol 1",
            sport_type="Futbol",
            space_number=1,
            composite_code=build_sports_space_code(
                venue_name=venue.name,
                venue_address=venue.address,
                sport_type="Futbol",
                space_number=1,
            ),
            is_active=True,
        )
    )
    session.commit()

    result = seed_demo_data(session)

    assert result.venues_created == 3
    assert result.spaces_created == 23
    assert session.scalar(select(func.count()).select_from(Venue)) == 4
    assert session.scalar(select(func.count()).select_from(SportsSpace)) == 24
    session.close()


def test_seed_rolls_back_all_changes_when_commit_fails(monkeypatch) -> None:
    session = create_database_session()

    def fail_commit() -> None:
        raise RuntimeError("error de prueba")

    monkeypatch.setattr(session, "commit", fail_commit)

    try:
        seed_demo_data(session)
    except RuntimeError as error:
        assert str(error) == "error de prueba"
    else:
        raise AssertionError("El seed debia propagar el error de commit.")

    assert session.scalar(select(func.count()).select_from(Venue)) == 0
    assert session.scalar(select(func.count()).select_from(SportsSpace)) == 0
    session.close()


def test_seed_does_not_create_users_reservations_devices_or_reminders() -> None:
    session = create_database_session()

    seed_demo_data(session)

    assert session.scalar(select(func.count()).select_from(User)) == 0
    assert session.scalar(select(func.count()).select_from(Reservation)) == 0
    assert session.scalar(select(func.count()).select_from(PushDevice)) == 0
    assert session.scalar(select(func.count()).select_from(ReservationReminder)) == 0
    session.close()
