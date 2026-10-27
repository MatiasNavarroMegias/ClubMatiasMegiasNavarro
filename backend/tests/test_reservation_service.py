from datetime import UTC, datetime, time, timedelta
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from app.models import Reservation, SportsSpace, Venue
from app.repositories import (
    ReservationRepository,
    SportsSpaceRepository,
)
from app.schemas import ReservationCreate
from app.services import (
    ReservationInvalidStartTimeError,
    ReservationOutsideVenueHoursError,
    ReservationService,
    ReservationSportsSpaceInactiveError,
    ReservationSportsSpaceNotFoundError,
    ReservationStartInPastError,
    ReservationTimeConflictError,
    ReservationVenueInactiveError,
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


def create_venue(
    *,
    opening_time: time = time(8, 0),
    closing_time: time = time(23, 0),
    is_active: bool = True,
) -> Venue:
    """
    Construye una sede reutilizable para las pruebas.
    """
    return Venue(
        id=1,
        name="Sede Ramos Mejia",
        address="Avenida de Mayo 1000",
        opening_time=opening_time,
        closing_time=closing_time,
        is_active=is_active,
    )


def create_sports_space(
    *,
    sports_space_id: int = 8,
    is_active: bool = True,
    venue: Venue | None = None,
) -> SportsSpace:
    """
    Construye un espacio deportivo asociado con una sede.
    """
    return SportsSpace(
        id=sports_space_id,
        venue_id=1,
        name="Cancha de Futbol 1",
        sport_type="Futbol",
        space_number=1,
        is_active=is_active,
        venue=venue or create_venue(),
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


def create_reservation_data(
    *,
    start_at: datetime | None = None,
) -> ReservationCreate:
    """
    Construye los datos de una reserva futura valida.
    """
    return ReservationCreate(
        sports_space_id=8,
        start_at=start_at
        or datetime(
            2026,
            11,
            3,
            18,
            0,
            tzinfo=APPLICATION_TIMEZONE,
        ),
    )


def test_create_reservation_builds_confirmed_one_hour_reservation() -> None:
    """
    Verifica la creacion completa de una reserva valida.
    """
    service, reservation_repository, sports_repository = create_service()

    sports_space = create_sports_space()
    sports_repository.get_by_id.return_value = sports_space
    reservation_repository.get_overlapping_confirmed.return_value = None
    reservation_repository.add.side_effect = lambda reservation: reservation

    result = service.create_reservation(
        user_id=5,
        reservation_data=create_reservation_data(),
    )

    assert result.user_id == 5
    assert result.sports_space_id == 8
    assert result.start_at == datetime(
        2026,
        11,
        3,
        18,
        0,
        tzinfo=APPLICATION_TIMEZONE,
    )
    assert result.end_at == datetime(
        2026,
        11,
        3,
        19,
        0,
        tzinfo=APPLICATION_TIMEZONE,
    )
    assert result.status == "confirmed"
    assert result.cancelled_at is None

    sports_repository.get_by_id.assert_called_once_with(8)
    reservation_repository.get_overlapping_confirmed.assert_called_once_with(
        sports_space_id=8,
        start_at=result.start_at,
        end_at=result.end_at,
    )
    reservation_repository.add.assert_called_once_with(result)


def test_create_reservation_uses_authenticated_user_id() -> None:
    """
    Verifica que el propietario provenga de la autenticacion.
    """
    service, reservation_repository, sports_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space()
    reservation_repository.get_overlapping_confirmed.return_value = None
    reservation_repository.add.side_effect = lambda reservation: reservation

    result = service.create_reservation(
        user_id=25,
        reservation_data=create_reservation_data(),
    )

    assert result.user_id == 25


def test_create_reservation_converts_utc_start_to_local_timezone() -> None:
    """
    Verifica la conversion de UTC a la zona local configurada.
    """
    service, reservation_repository, sports_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space()
    reservation_repository.get_overlapping_confirmed.return_value = None
    reservation_repository.add.side_effect = lambda reservation: reservation

    reservation_data = create_reservation_data(
        start_at=datetime(
            2026,
            11,
            3,
            21,
            0,
            tzinfo=UTC,
        ),
    )

    result = service.create_reservation(
        user_id=5,
        reservation_data=reservation_data,
    )

    assert result.start_at == datetime(
        2026,
        11,
        3,
        18,
        0,
        tzinfo=APPLICATION_TIMEZONE,
    )
    assert result.end_at.hour == 19


def test_create_reservation_rejects_missing_sports_space() -> None:
    """
    Verifica el error para un espacio inexistente.
    """
    service, reservation_repository, sports_repository = create_service()
    sports_repository.get_by_id.return_value = None

    with pytest.raises(
        ReservationSportsSpaceNotFoundError,
        match="identificador 8",
    ):
        service.create_reservation(
            user_id=5,
            reservation_data=create_reservation_data(),
        )

    reservation_repository.get_overlapping_confirmed.assert_not_called()
    reservation_repository.add.assert_not_called()


def test_create_reservation_rejects_inactive_sports_space() -> None:
    """
    Verifica que un espacio inactivo no pueda reservarse.
    """
    service, reservation_repository, sports_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space(
        is_active=False,
    )

    with pytest.raises(
        ReservationSportsSpaceInactiveError,
        match="espacio deportivo se encuentra inactivo",
    ):
        service.create_reservation(
            user_id=5,
            reservation_data=create_reservation_data(),
        )

    reservation_repository.get_overlapping_confirmed.assert_not_called()
    reservation_repository.add.assert_not_called()


def test_create_reservation_rejects_inactive_venue() -> None:
    """
    Verifica que una sede inactiva no permita reservas.
    """
    service, reservation_repository, sports_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space(
        venue=create_venue(
            is_active=False,
        ),
    )

    with pytest.raises(
        ReservationVenueInactiveError,
        match="sede del espacio deportivo se encuentra inactiva",
    ):
        service.create_reservation(
            user_id=5,
            reservation_data=create_reservation_data(),
        )

    reservation_repository.get_overlapping_confirmed.assert_not_called()
    reservation_repository.add.assert_not_called()


@pytest.mark.parametrize(
    "start_at",
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
def test_create_reservation_rejects_past_or_current_start(
    start_at: datetime,
) -> None:
    """
    Verifica que el turno deba comenzar después del momento actual.
    """
    service, reservation_repository, sports_repository = create_service()
    sports_repository.get_by_id.return_value = create_sports_space()

    with pytest.raises(
        ReservationStartInPastError,
        match="debe pertenecer al futuro",
    ):
        service.create_reservation(
            user_id=5,
            reservation_data=create_reservation_data(
                start_at=start_at,
            ),
        )

    reservation_repository.get_overlapping_confirmed.assert_not_called()
    reservation_repository.add.assert_not_called()


@pytest.mark.parametrize(
    "start_at",
    [
        datetime(
            2026,
            11,
            3,
            18,
            30,
            tzinfo=APPLICATION_TIMEZONE,
        ),
        datetime(
            2026,
            11,
            3,
            18,
            0,
            15,
            tzinfo=APPLICATION_TIMEZONE,
        ),
        datetime(
            2026,
            11,
            3,
            18,
            0,
            0,
            500000,
            tzinfo=APPLICATION_TIMEZONE,
        ),
    ],
)
def test_create_reservation_rejects_non_full_hour(
    start_at: datetime,
) -> None:
    """
    Verifica el rechazo de minutos, segundos y microsegundos.
    """
    service, reservation_repository, sports_repository = create_service()
    sports_repository.get_by_id.return_value = create_sports_space()

    with pytest.raises(
        ReservationInvalidStartTimeError,
        match="hora completa",
    ):
        service.create_reservation(
            user_id=5,
            reservation_data=create_reservation_data(
                start_at=start_at,
            ),
        )

    reservation_repository.get_overlapping_confirmed.assert_not_called()
    reservation_repository.add.assert_not_called()


def test_create_reservation_rejects_start_before_opening() -> None:
    """
    Verifica un turno que comienza antes de la apertura.
    """
    service, reservation_repository, sports_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space(
        venue=create_venue(
            opening_time=time(8, 0),
            closing_time=time(23, 0),
        ),
    )

    with pytest.raises(
        ReservationOutsideVenueHoursError,
        match="fuera del horario",
    ):
        service.create_reservation(
            user_id=5,
            reservation_data=create_reservation_data(
                start_at=datetime(
                    2026,
                    11,
                    3,
                    7,
                    0,
                    tzinfo=APPLICATION_TIMEZONE,
                ),
            ),
        )

    reservation_repository.get_overlapping_confirmed.assert_not_called()
    reservation_repository.add.assert_not_called()


def test_create_reservation_rejects_end_after_closing() -> None:
    """
    Verifica un turno que finaliza después del cierre.
    """
    service, reservation_repository, sports_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space(
        venue=create_venue(
            opening_time=time(8, 0),
            closing_time=time(23, 0),
        ),
    )

    with pytest.raises(
        ReservationOutsideVenueHoursError,
        match="fuera del horario",
    ):
        service.create_reservation(
            user_id=5,
            reservation_data=create_reservation_data(
                start_at=datetime(
                    2026,
                    11,
                    3,
                    23,
                    0,
                    tzinfo=APPLICATION_TIMEZONE,
                ),
            ),
        )

    reservation_repository.get_overlapping_confirmed.assert_not_called()
    reservation_repository.add.assert_not_called()


@pytest.mark.parametrize(
    "start_hour",
    [
        8,
        22,
    ],
)
def test_create_reservation_accepts_boundary_slots(
    start_hour: int,
) -> None:
    """
    Verifica el primer y el último turno permitidos.
    """
    service, reservation_repository, sports_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space(
        venue=create_venue(
            opening_time=time(8, 0),
            closing_time=time(23, 0),
        ),
    )
    reservation_repository.get_overlapping_confirmed.return_value = None
    reservation_repository.add.side_effect = lambda reservation: reservation

    result = service.create_reservation(
        user_id=5,
        reservation_data=create_reservation_data(
            start_at=datetime(
                2026,
                11,
                3,
                start_hour,
                0,
                tzinfo=APPLICATION_TIMEZONE,
            ),
        ),
    )

    assert result.start_at.hour == start_hour
    assert result.end_at.hour == start_hour + 1


def test_create_reservation_rejects_overlapping_reservation() -> None:
    """
    Verifica que un turno ocupado no pueda reservarse.
    """
    service, reservation_repository, sports_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space()

    requested_start = datetime(
        2026,
        11,
        3,
        18,
        0,
        tzinfo=APPLICATION_TIMEZONE,
    )

    reservation_repository.get_overlapping_confirmed.return_value = Reservation(
        id=1,
        user_id=9,
        sports_space_id=8,
        start_at=requested_start,
        end_at=requested_start + timedelta(hours=1),
        status="confirmed",
        cancelled_at=None,
    )

    with pytest.raises(
        ReservationTimeConflictError,
        match="ya se encuentra reservado",
    ):
        service.create_reservation(
            user_id=5,
            reservation_data=create_reservation_data(
                start_at=requested_start,
            ),
        )

    reservation_repository.add.assert_not_called()


def test_create_reservation_accepts_slot_without_overlap() -> None:
    """
    Verifica que un turno libre pueda persistirse.

    El repositorio aplica la fórmula de superposición, por lo que un
    turno consecutivo produce None y no bloquea la creación.
    """
    service, reservation_repository, sports_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space()
    reservation_repository.get_overlapping_confirmed.return_value = None
    reservation_repository.add.side_effect = lambda reservation: reservation

    result = service.create_reservation(
        user_id=5,
        reservation_data=create_reservation_data(
            start_at=datetime(
                2026,
                11,
                3,
                19,
                0,
                tzinfo=APPLICATION_TIMEZONE,
            ),
        ),
    )

    assert result.start_at.hour == 19
    assert result.end_at.hour == 20
    reservation_repository.add.assert_called_once_with(result)


def test_create_reservation_rejects_naive_current_datetime() -> None:
    """
    Verifica que el reloj inyectado incluya zona horaria.
    """
    service, reservation_repository, sports_repository = create_service(
        current_datetime=datetime(
            2026,
            11,
            2,
            10,
            30,
        ),
    )

    sports_repository.get_by_id.return_value = create_sports_space()

    with pytest.raises(
        ValueError,
        match="proveedor de fecha actual debe devolver",
    ):
        service.create_reservation(
            user_id=5,
            reservation_data=create_reservation_data(),
        )

    reservation_repository.get_overlapping_confirmed.assert_not_called()
    reservation_repository.add.assert_not_called()
