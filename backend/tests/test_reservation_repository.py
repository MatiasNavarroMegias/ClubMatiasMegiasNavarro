from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models import Reservation
from app.repositories import ReservationRepository


def create_reservation(
    *,
    reservation_id: int = 1,
    user_id: int = 5,
    sports_space_id: int = 8,
    start_at: datetime | None = None,
    status: str = "confirmed",
) -> Reservation:
    """
    Construye una reserva reutilizable sin acceder a PostgreSQL.

    Los valores pueden reemplazarse para representar reservas futuras,
    finalizadas o canceladas.
    """
    reservation_start = start_at or datetime(
        2026,
        11,
        2,
        18,
        0,
        tzinfo=UTC,
    )

    cancelled_at = None

    if status == "cancelled":
        cancelled_at = datetime(
            2026,
            10,
            30,
            10,
            15,
            tzinfo=UTC,
        )

    return Reservation(
        id=reservation_id,
        user_id=user_id,
        sports_space_id=sports_space_id,
        start_at=reservation_start,
        end_at=reservation_start + timedelta(hours=1),
        status=status,
        cancelled_at=cancelled_at,
    )


def create_repository() -> tuple[
    ReservationRepository,
    MagicMock,
]:
    """
    Crea un repositorio conectado con una sesion simulada.

    Esto permite comprobar las consultas construidas por SQLAlchemy
    sin ejecutar operaciones reales contra PostgreSQL.
    """
    database_session = MagicMock(spec=Session)

    repository = ReservationRepository(
        database_session,
    )

    return repository, database_session


def test_get_by_id_returns_existing_reservation() -> None:
    """
    Verifica la consulta de una reserva mediante su clave primaria.
    """
    repository, database_session = create_repository()
    expected_reservation = create_reservation()

    database_session.get.return_value = expected_reservation

    reservation = repository.get_by_id(1)

    assert reservation is expected_reservation
    database_session.get.assert_called_once_with(
        Reservation,
        1,
    )


def test_get_by_id_returns_none_when_reservation_does_not_exist() -> None:
    """
    Verifica que un identificador inexistente devuelva None.
    """
    repository, database_session = create_repository()
    database_session.get.return_value = None

    reservation = repository.get_by_id(999)

    assert reservation is None
    database_session.get.assert_called_once_with(
        Reservation,
        999,
    )


def test_get_by_id_and_user_filters_reservation_owner() -> None:
    """
    Verifica que la consulta incluya la reserva y su propietario.
    """
    repository, database_session = create_repository()
    expected_reservation = create_reservation()

    database_session.scalar.return_value = expected_reservation

    reservation = repository.get_by_id_and_user(
        reservation_id=1,
        user_id=5,
    )

    assert reservation is expected_reservation
    database_session.scalar.assert_called_once()

    statement = database_session.scalar.call_args.args[0]
    statement_text = str(statement)
    parameters = statement.compile().params

    assert "reservations.id" in statement_text
    assert "reservations.user_id" in statement_text
    assert 1 in parameters.values()
    assert 5 in parameters.values()


def test_get_by_id_and_user_returns_none_for_another_owner() -> None:
    """
    Verifica que una reserva ajena no sea devuelta.
    """
    repository, database_session = create_repository()
    database_session.scalar.return_value = None

    reservation = repository.get_by_id_and_user(
        reservation_id=1,
        user_id=999,
    )

    assert reservation is None
    database_session.scalar.assert_called_once()


def test_get_overlapping_confirmed_builds_expected_query() -> None:
    """
    Verifica la formula utilizada para detectar superposiciones.

    Una reserva existente se superpone cuando comienza antes del final
    solicitado y termina despues del inicio solicitado.
    """
    repository, database_session = create_repository()

    start_at = datetime(
        2026,
        11,
        2,
        18,
        0,
        tzinfo=UTC,
    )
    end_at = start_at + timedelta(hours=1)

    expected_reservation = create_reservation(
        start_at=start_at,
    )

    database_session.scalar.return_value = expected_reservation

    reservation = repository.get_overlapping_confirmed(
        sports_space_id=8,
        start_at=start_at,
        end_at=end_at,
    )

    assert reservation is expected_reservation
    database_session.scalar.assert_called_once()

    statement = database_session.scalar.call_args.args[0]
    statement_text = str(statement)
    parameters = statement.compile().params

    assert "reservations.sports_space_id" in statement_text
    assert "reservations.status" in statement_text
    assert "reservations.start_at <" in statement_text
    assert "reservations.end_at >" in statement_text

    assert 8 in parameters.values()
    assert "confirmed" in parameters.values()
    assert start_at in parameters.values()
    assert end_at in parameters.values()


def test_get_overlapping_confirmed_returns_none_when_slot_is_available() -> None:
    """
    Verifica el resultado cuando no existe ninguna superposicion.
    """
    repository, database_session = create_repository()
    database_session.scalar.return_value = None

    start_at = datetime(
        2026,
        11,
        2,
        19,
        0,
        tzinfo=UTC,
    )

    reservation = repository.get_overlapping_confirmed(
        sports_space_id=8,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
    )

    assert reservation is None
    database_session.scalar.assert_called_once()


def test_list_confirmed_for_space_between_returns_reservations() -> None:
    """
    Verifica la consulta de reservas confirmadas dentro de un rango.
    """
    repository, database_session = create_repository()

    expected_reservations = [
        create_reservation(
            reservation_id=1,
            start_at=datetime(
                2026,
                11,
                2,
                18,
                0,
                tzinfo=UTC,
            ),
        ),
        create_reservation(
            reservation_id=2,
            start_at=datetime(
                2026,
                11,
                2,
                20,
                0,
                tzinfo=UTC,
            ),
        ),
    ]

    database_session.scalars.return_value.all.return_value = expected_reservations

    range_start = datetime(
        2026,
        11,
        2,
        0,
        0,
        tzinfo=UTC,
    )
    range_end = range_start + timedelta(days=1)

    reservations = repository.list_confirmed_for_space_between(
        sports_space_id=8,
        range_start=range_start,
        range_end=range_end,
    )

    assert reservations == expected_reservations
    database_session.scalars.assert_called_once()

    statement = database_session.scalars.call_args.args[0]
    statement_text = str(statement)
    parameters = statement.compile().params

    assert "reservations.sports_space_id" in statement_text
    assert "reservations.status" in statement_text
    assert "reservations.start_at <" in statement_text
    assert "reservations.end_at >" in statement_text
    assert "ORDER BY reservations.start_at" in statement_text

    assert 8 in parameters.values()
    assert "confirmed" in parameters.values()
    assert range_start in parameters.values()
    assert range_end in parameters.values()


def test_list_upcoming_by_user_returns_future_confirmed_reservations() -> None:
    """
    Verifica la consulta de proximas reservas del usuario.
    """
    repository, database_session = create_repository()

    expected_reservations = [
        create_reservation(
            reservation_id=1,
            start_at=datetime(
                2026,
                11,
                2,
                18,
                0,
                tzinfo=UTC,
            ),
        ),
        create_reservation(
            reservation_id=2,
            start_at=datetime(
                2026,
                11,
                3,
                18,
                0,
                tzinfo=UTC,
            ),
        ),
    ]

    database_session.scalars.return_value.all.return_value = expected_reservations

    from_at = datetime(
        2026,
        10,
        27,
        12,
        0,
        tzinfo=UTC,
    )

    reservations = repository.list_upcoming_by_user(
        user_id=5,
        from_at=from_at,
    )

    assert reservations == expected_reservations
    database_session.scalars.assert_called_once()

    statement = database_session.scalars.call_args.args[0]
    statement_text = str(statement)
    parameters = statement.compile().params

    assert "reservations.user_id" in statement_text
    assert "reservations.status" in statement_text
    assert "reservations.start_at >=" in statement_text
    assert "ORDER BY reservations.start_at" in statement_text

    assert 5 in parameters.values()
    assert "confirmed" in parameters.values()
    assert from_at in parameters.values()


def test_list_history_by_user_includes_cancelled_and_finished() -> None:
    """
    Verifica la consulta del historial del usuario.

    El historial incluye reservas canceladas y reservas cuyo horario
    de finalizacion ya paso.
    """
    repository, database_session = create_repository()

    expected_reservations = [
        create_reservation(
            reservation_id=2,
            status="cancelled",
        ),
        create_reservation(
            reservation_id=1,
            start_at=datetime(
                2026,
                10,
                20,
                18,
                0,
                tzinfo=UTC,
            ),
        ),
    ]

    database_session.scalars.return_value.all.return_value = expected_reservations

    before_at = datetime(
        2026,
        10,
        27,
        12,
        0,
        tzinfo=UTC,
    )

    reservations = repository.list_history_by_user(
        user_id=5,
        before_at=before_at,
    )

    assert reservations == expected_reservations
    database_session.scalars.assert_called_once()

    statement = database_session.scalars.call_args.args[0]
    statement_text = str(statement)
    parameters = statement.compile().params

    assert "reservations.user_id" in statement_text
    assert "reservations.status" in statement_text
    assert "reservations.end_at <=" in statement_text
    assert " OR " in statement_text
    assert "ORDER BY reservations.start_at DESC" in statement_text

    assert 5 in parameters.values()
    assert "cancelled" in parameters.values()
    assert before_at in parameters.values()


def test_add_persists_and_refreshes_reservation() -> None:
    """
    Verifica que add agregue, confirme y recargue una reserva.
    """
    repository, database_session = create_repository()
    reservation = create_reservation()

    result = repository.add(
        reservation,
    )

    assert result is reservation
    database_session.add.assert_called_once_with(
        reservation,
    )
    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(
        reservation,
    )


def test_save_commits_and_refreshes_existing_reservation() -> None:
    """
    Verifica la persistencia de una reserva existente.
    """
    repository, database_session = create_repository()

    reservation = create_reservation(
        status="cancelled",
    )

    result = repository.save(
        reservation,
    )

    assert result is reservation
    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(
        reservation,
    )
    database_session.add.assert_not_called()
