from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from app.models import Reservation
from app.repositories import (
    ReservationRepository,
    SportsSpaceRepository,
)
from app.services import (
    ReservationAlreadyCancelledError,
    ReservationAlreadyStartedError,
    ReservationNotFoundError,
    ReservationService,
)

APPLICATION_TIMEZONE = ZoneInfo(
    "America/Argentina/Buenos_Aires",
)

CURRENT_DATETIME = datetime(
    2026,
    11,
    2,
    10,
    30,
    tzinfo=APPLICATION_TIMEZONE,
)


def create_reservation(
    *,
    reservation_id: int = 1,
    user_id: int = 7,
    start_at: datetime | None = None,
    status: str = "confirmed",
    cancelled_at: datetime | None = None,
) -> Reservation:
    """
    Construye una reserva reutilizable para las pruebas.

    La reserva no se persiste en PostgreSQL. Los valores pueden
    reemplazarse para representar reservas futuras, finalizadas o
    canceladas.
    """
    reservation_start = start_at or datetime(
        2026,
        11,
        3,
        18,
        0,
        tzinfo=APPLICATION_TIMEZONE,
    )

    return Reservation(
        id=reservation_id,
        user_id=user_id,
        sports_space_id=8,
        start_at=reservation_start,
        end_at=reservation_start + timedelta(hours=1),
        status=status,
        cancelled_at=cancelled_at,
    )


def create_service(
    *,
    current_datetime: datetime = CURRENT_DATETIME,
) -> tuple[
    ReservationService,
    MagicMock,
    MagicMock,
]:
    """
    Crea el servicio con repositorios y reloj simulados.
    """
    reservation_repository = MagicMock(
        spec=ReservationRepository,
    )
    sports_space_repository = MagicMock(
        spec=SportsSpaceRepository,
    )

    service = ReservationService(
        reservation_repository=reservation_repository,
        sports_space_repository=sports_space_repository,
        timezone=APPLICATION_TIMEZONE,
        now_provider=lambda: current_datetime,
    )

    return (
        service,
        reservation_repository,
        sports_space_repository,
    )


def test_list_upcoming_reservations_forwards_user_and_current_time() -> None:
    """
    Verifica la consulta de proximas reservas del usuario.
    """
    service, reservation_repository, _ = create_service()

    expected_reservations = [
        create_reservation(
            reservation_id=1,
        ),
        create_reservation(
            reservation_id=2,
            start_at=datetime(
                2026,
                11,
                4,
                18,
                0,
                tzinfo=APPLICATION_TIMEZONE,
            ),
        ),
    ]

    reservation_repository.list_upcoming_by_user.return_value = expected_reservations

    reservations = service.list_upcoming_reservations(
        user_id=7,
    )

    assert reservations == expected_reservations

    reservation_repository.list_upcoming_by_user.assert_called_once_with(
        user_id=7,
        from_at=CURRENT_DATETIME,
    )


def test_list_reservation_history_forwards_user_and_current_time() -> None:
    """
    Verifica la consulta del historial del usuario.
    """
    service, reservation_repository, _ = create_service()

    expected_reservations = [
        create_reservation(
            reservation_id=2,
            status="cancelled",
            cancelled_at=datetime(
                2026,
                11,
                1,
                12,
                0,
                tzinfo=APPLICATION_TIMEZONE,
            ),
        ),
        create_reservation(
            reservation_id=1,
            start_at=datetime(
                2026,
                10,
                30,
                18,
                0,
                tzinfo=APPLICATION_TIMEZONE,
            ),
        ),
    ]

    reservation_repository.list_history_by_user.return_value = expected_reservations

    reservations = service.list_reservation_history(
        user_id=7,
    )

    assert reservations == expected_reservations

    reservation_repository.list_history_by_user.assert_called_once_with(
        user_id=7,
        before_at=CURRENT_DATETIME,
    )


def test_cancel_reservation_rejects_missing_or_foreign_reservation() -> None:
    """
    Verifica una reserva inexistente o perteneciente a otro usuario.
    """
    service, reservation_repository, _ = create_service()

    reservation_repository.get_by_id_and_user.return_value = None

    with pytest.raises(
        ReservationNotFoundError,
        match="identificador 999",
    ):
        service.cancel_reservation(
            reservation_id=999,
            user_id=7,
        )

    reservation_repository.get_by_id_and_user.assert_called_once_with(
        reservation_id=999,
        user_id=7,
    )
    reservation_repository.save.assert_not_called()


def test_cancel_reservation_rejects_already_cancelled_reservation() -> None:
    """
    Verifica que una reserva cancelada no se cancele nuevamente.
    """
    service, reservation_repository, _ = create_service()

    cancellation_time = datetime(
        2026,
        11,
        1,
        12,
        0,
        tzinfo=APPLICATION_TIMEZONE,
    )

    reservation_repository.get_by_id_and_user.return_value = create_reservation(
        status="cancelled",
        cancelled_at=cancellation_time,
    )

    with pytest.raises(
        ReservationAlreadyCancelledError,
        match="ya se encuentra cancelada",
    ):
        service.cancel_reservation(
            reservation_id=1,
            user_id=7,
        )

    reservation_repository.save.assert_not_called()


@pytest.mark.parametrize(
    "reservation_start",
    [
        datetime(
            2026,
            11,
            2,
            9,
            0,
            tzinfo=APPLICATION_TIMEZONE,
        ),
        CURRENT_DATETIME,
    ],
)
def test_cancel_reservation_rejects_started_reservation(
    reservation_start: datetime,
) -> None:
    """
    Verifica reservas iniciadas o con inicio igual al momento actual.
    """
    service, reservation_repository, _ = create_service()

    reservation_repository.get_by_id_and_user.return_value = create_reservation(
        start_at=reservation_start,
    )

    with pytest.raises(
        ReservationAlreadyStartedError,
        match="ya comenzo",
    ):
        service.cancel_reservation(
            reservation_id=1,
            user_id=7,
        )

    reservation_repository.save.assert_not_called()


def test_cancel_reservation_updates_status_and_cancellation_time() -> None:
    """
    Verifica la cancelacion logica de una reserva futura.
    """
    service, reservation_repository, _ = create_service()

    reservation = create_reservation()

    reservation_repository.get_by_id_and_user.return_value = reservation
    reservation_repository.save.side_effect = lambda saved_reservation: saved_reservation

    result = service.cancel_reservation(
        reservation_id=1,
        user_id=7,
    )

    assert result is reservation
    assert result.status == "cancelled"
    assert result.cancelled_at == CURRENT_DATETIME

    reservation_repository.save.assert_called_once_with(
        reservation,
    )


def test_cancel_reservation_preserves_other_reservation_data() -> None:
    """
    Verifica que la cancelacion no modifique el turno ni el propietario.
    """
    service, reservation_repository, _ = create_service()

    reservation = create_reservation(
        reservation_id=5,
        user_id=7,
    )

    original_start_at = reservation.start_at
    original_end_at = reservation.end_at
    original_sports_space_id = reservation.sports_space_id

    reservation_repository.get_by_id_and_user.return_value = reservation
    reservation_repository.save.side_effect = lambda saved_reservation: saved_reservation

    result = service.cancel_reservation(
        reservation_id=5,
        user_id=7,
    )

    assert result.id == 5
    assert result.user_id == 7
    assert result.sports_space_id == original_sports_space_id
    assert result.start_at == original_start_at
    assert result.end_at == original_end_at


def test_cancel_reservation_converts_utc_start_before_validation() -> None:
    """
    Verifica una fecha de reserva almacenada en UTC.

    Las 15:00 UTC representan las 12:00 en Buenos Aires, por lo que
    la reserva todavia es futura respecto de las 10:30 locales.
    """
    service, reservation_repository, _ = create_service()

    reservation = create_reservation(
        start_at=datetime(
            2026,
            11,
            2,
            15,
            0,
            tzinfo=UTC,
        ),
    )

    reservation_repository.get_by_id_and_user.return_value = reservation
    reservation_repository.save.side_effect = lambda saved_reservation: saved_reservation

    result = service.cancel_reservation(
        reservation_id=1,
        user_id=7,
    )

    assert result.status == "cancelled"
    assert result.cancelled_at == CURRENT_DATETIME
    reservation_repository.save.assert_called_once_with(
        reservation,
    )


def test_cancelled_reservation_no_longer_has_confirmed_status() -> None:
    """
    Verifica que una cancelacion libere logicamente el horario.

    Las consultas de disponibilidad solo consideran reservas con
    estado confirmed. Por eso cambiar a cancelled deja de bloquear
    el turno sin eliminar el registro.
    """
    service, reservation_repository, _ = create_service()

    reservation = create_reservation()

    reservation_repository.get_by_id_and_user.return_value = reservation
    reservation_repository.save.side_effect = lambda saved_reservation: saved_reservation

    result = service.cancel_reservation(
        reservation_id=1,
        user_id=7,
    )

    assert result.status != "confirmed"
    assert result.status == "cancelled"
    assert result.cancelled_at is not None


def test_lifecycle_methods_reject_naive_current_datetime() -> None:
    """
    Verifica que las consultas utilicen un reloj con zona horaria.
    """
    naive_datetime = datetime(
        2026,
        11,
        2,
        10,
        30,
    )

    service, reservation_repository, _ = create_service(
        current_datetime=naive_datetime,
    )

    with pytest.raises(
        ValueError,
        match="proveedor de fecha actual debe devolver",
    ):
        service.list_upcoming_reservations(
            user_id=7,
        )

    reservation_repository.list_upcoming_by_user.assert_not_called()
