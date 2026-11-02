from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Reservation, SportsSpace, User, Venue
from app.scripts.seed_demo_data import seed_demo_data


def create_database_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_seed_creates_demo_venue_and_spaces() -> None:
    session = create_database_session()

    result = seed_demo_data(session)

    assert result.venues_created == 1
    assert result.spaces_created == 3
    assert session.scalar(select(func.count()).select_from(Venue)) == 1
    assert session.scalar(select(func.count()).select_from(SportsSpace)) == 3
    codes = set(session.scalars(select(SportsSpace.composite_code)).all())
    assert codes == {
        "Sede_Moron_Rivadavia_19850_Futbol_1",
        "Sede_Moron_Rivadavia_19850_Futbol_2",
        "Sede_Moron_Rivadavia_19850_Paddle_1",
    }

    session.close()


def test_seed_is_idempotent_and_does_not_duplicate_data() -> None:
    session = create_database_session()

    first_result = seed_demo_data(session)
    second_result = seed_demo_data(session)

    assert first_result.venues_created == 1
    assert first_result.spaces_created == 3
    assert second_result.venues_created == 0
    assert second_result.spaces_created == 0
    assert session.scalar(select(func.count()).select_from(Venue)) == 1
    assert session.scalar(select(func.count()).select_from(SportsSpace)) == 3

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


def test_seed_does_not_create_users_or_reservations() -> None:
    session = create_database_session()

    seed_demo_data(session)

    assert len(session.new) == 0
    assert session.scalar(select(func.count()).select_from(User)) == 0
    assert session.scalar(select(func.count()).select_from(Reservation)) == 0
    session.close()
