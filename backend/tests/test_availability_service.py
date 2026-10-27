from datetime import UTC, date, datetime, time, timedelta
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from app.models import Reservation, SportsSpace, Venue
from app.repositories import (
    ReservationRepository,
    SportsSpaceRepository,
)
from app.services import (
    AvailabilityDateInPastError,
    AvailabilityService,
    AvailabilitySportsSpaceInactiveError,
    AvailabilitySportsSpaceNotFoundError,
    AvailabilityVenueInactiveError,
)

APPLICATION_TIMEZONE = ZoneInfo(
    "America/Argentina/Buenos_Aires",
)


def create_venue(
    *,
    opening_time: time = time(8, 0),
    closing_time: time = time(12, 0),
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


def create_reservation(
    *,
    start_at: datetime,
    sports_space_id: int = 8,
) -> Reservation:
    """
    Construye una reserva confirmada de una hora.
    """
    return Reservation(
        id=1,
        user_id=5,
        sports_space_id=sports_space_id,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
        status="confirmed",
        cancelled_at=None,
    )


def create_service(
    *,
    current_datetime: datetime | None = None,
) -> tuple[
    AvailabilityService,
    MagicMock,
    MagicMock,
]:
    """
    Crea el servicio con repositorios y reloj simulados.
    """
    sports_space_repository = MagicMock(
        spec=SportsSpaceRepository,
    )
    reservation_repository = MagicMock(
        spec=ReservationRepository,
    )

    fixed_current_datetime = current_datetime or datetime(
        2026,
        11,
        2,
        10,
        30,
        tzinfo=APPLICATION_TIMEZONE,
    )

    service = AvailabilityService(
        sports_space_repository=sports_space_repository,
        reservation_repository=reservation_repository,
        timezone=APPLICATION_TIMEZONE,
        now_provider=lambda: fixed_current_datetime,
    )

    return (
        service,
        sports_space_repository,
        reservation_repository,
    )


def test_list_available_slots_returns_all_slots_for_future_date() -> None:
    """
    Verifica la generacion de turnos para una fecha futura.
    """
    service, sports_repository, reservation_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space()
    reservation_repository.list_confirmed_for_space_between.return_value = []

    slots = service.list_available_slots(
        sports_space_id=8,
        selected_date=date(2026, 11, 3),
    )

    assert [slot.start_at.hour for slot in slots] == [
        8,
        9,
        10,
        11,
    ]
    assert [slot.end_at.hour for slot in slots] == [
        9,
        10,
        11,
        12,
    ]

    for slot in slots:
        assert slot.start_at.tzinfo is APPLICATION_TIMEZONE
        assert slot.end_at - slot.start_at == timedelta(
            hours=1,
        )


def test_list_available_slots_rejects_missing_sports_space() -> None:
    """
    Verifica el error para un espacio inexistente.
    """
    service, sports_repository, reservation_repository = create_service()
    sports_repository.get_by_id.return_value = None

    with pytest.raises(
        AvailabilitySportsSpaceNotFoundError,
        match="identificador 999",
    ):
        service.list_available_slots(
            sports_space_id=999,
            selected_date=date(2026, 11, 3),
        )

    sports_repository.get_by_id.assert_called_once_with(999)
    reservation_repository.list_confirmed_for_space_between.assert_not_called()


def test_list_available_slots_rejects_inactive_sports_space() -> None:
    """
    Verifica que un espacio inactivo no ofrezca turnos.
    """
    service, sports_repository, reservation_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space(
        is_active=False,
    )

    with pytest.raises(
        AvailabilitySportsSpaceInactiveError,
        match="espacio deportivo se encuentra inactivo",
    ):
        service.list_available_slots(
            sports_space_id=8,
            selected_date=date(2026, 11, 3),
        )

    reservation_repository.list_confirmed_for_space_between.assert_not_called()


def test_list_available_slots_rejects_inactive_venue() -> None:
    """
    Verifica que una sede inactiva no ofrezca turnos.
    """
    service, sports_repository, reservation_repository = create_service()

    inactive_venue = create_venue(
        is_active=False,
    )
    sports_repository.get_by_id.return_value = create_sports_space(
        venue=inactive_venue,
    )

    with pytest.raises(
        AvailabilityVenueInactiveError,
        match="sede del espacio deportivo se encuentra inactiva",
    ):
        service.list_available_slots(
            sports_space_id=8,
            selected_date=date(2026, 11, 3),
        )

    reservation_repository.list_confirmed_for_space_between.assert_not_called()


def test_list_available_slots_rejects_past_date() -> None:
    """
    Verifica que una fecha pasada sea rechazada.
    """
    service, sports_repository, reservation_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space()

    with pytest.raises(
        AvailabilityDateInPastError,
        match="fecha pasada",
    ):
        service.list_available_slots(
            sports_space_id=8,
            selected_date=date(2026, 11, 1),
        )

    reservation_repository.list_confirmed_for_space_between.assert_not_called()


def test_list_available_slots_excludes_past_slots_from_current_date() -> None:
    """
    Verifica que el dia actual excluya turnos ya iniciados.

    Si el momento actual es 10:30, solamente queda disponible el turno
    que comienza a las 11:00.
    """
    service, sports_repository, reservation_repository = create_service(
        current_datetime=datetime(
            2026,
            11,
            2,
            10,
            30,
            tzinfo=APPLICATION_TIMEZONE,
        ),
    )

    sports_repository.get_by_id.return_value = create_sports_space()
    reservation_repository.list_confirmed_for_space_between.return_value = []

    slots = service.list_available_slots(
        sports_space_id=8,
        selected_date=date(2026, 11, 2),
    )

    assert len(slots) == 1
    assert slots[0].start_at.hour == 11
    assert slots[0].end_at.hour == 12


def test_list_available_slots_excludes_occupied_slot() -> None:
    """
    Verifica que una reserva confirmada quite el turno ocupado.
    """
    service, sports_repository, reservation_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space()

    occupied_start = datetime(
        2026,
        11,
        3,
        9,
        0,
        tzinfo=APPLICATION_TIMEZONE,
    )
    reservation_repository.list_confirmed_for_space_between.return_value = [
        create_reservation(
            start_at=occupied_start,
        ),
    ]

    slots = service.list_available_slots(
        sports_space_id=8,
        selected_date=date(2026, 11, 3),
    )

    assert [slot.start_at.hour for slot in slots] == [
        8,
        10,
        11,
    ]


def test_list_available_slots_keeps_consecutive_slots_available() -> None:
    """
    Verifica que una reserva no bloquee turnos consecutivos.

    Una reserva de 09:00 a 10:00 no debe bloquear 08:00 a 09:00 ni
    10:00 a 11:00.
    """
    service, sports_repository, reservation_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space()

    reservation_repository.list_confirmed_for_space_between.return_value = [
        create_reservation(
            start_at=datetime(
                2026,
                11,
                3,
                9,
                0,
                tzinfo=APPLICATION_TIMEZONE,
            ),
        ),
    ]

    slots = service.list_available_slots(
        sports_space_id=8,
        selected_date=date(2026, 11, 3),
    )

    available_hours = [slot.start_at.hour for slot in slots]

    assert 8 in available_hours
    assert 9 not in available_hours
    assert 10 in available_hours


def test_list_available_slots_rounds_opening_to_next_full_hour() -> None:
    """
    Verifica una sede que abre en una hora con minutos.
    """
    service, sports_repository, reservation_repository = create_service()

    venue = create_venue(
        opening_time=time(8, 30),
        closing_time=time(12, 0),
    )
    sports_repository.get_by_id.return_value = create_sports_space(
        venue=venue,
    )
    reservation_repository.list_confirmed_for_space_between.return_value = []

    slots = service.list_available_slots(
        sports_space_id=8,
        selected_date=date(2026, 11, 3),
    )

    assert [slot.start_at.hour for slot in slots] == [
        9,
        10,
        11,
    ]


def test_list_available_slots_does_not_exceed_closing_time() -> None:
    """
    Verifica que ningún turno finalice después del cierre.
    """
    service, sports_repository, reservation_repository = create_service()

    venue = create_venue(
        opening_time=time(8, 0),
        closing_time=time(10, 30),
    )
    sports_repository.get_by_id.return_value = create_sports_space(
        venue=venue,
    )
    reservation_repository.list_confirmed_for_space_between.return_value = []

    slots = service.list_available_slots(
        sports_space_id=8,
        selected_date=date(2026, 11, 3),
    )

    assert [slot.start_at.hour for slot in slots] == [
        8,
        9,
    ]
    assert slots[-1].end_at.hour == 10


def test_list_available_slots_uses_complete_local_day_range() -> None:
    """
    Verifica el rango enviado al repositorio de reservas.
    """
    service, sports_repository, reservation_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space()
    reservation_repository.list_confirmed_for_space_between.return_value = []

    service.list_available_slots(
        sports_space_id=8,
        selected_date=date(2026, 11, 3),
    )

    reservation_repository.list_confirmed_for_space_between.assert_called_once_with(
        sports_space_id=8,
        range_start=datetime(
            2026,
            11,
            3,
            0,
            0,
            tzinfo=APPLICATION_TIMEZONE,
        ),
        range_end=datetime(
            2026,
            11,
            4,
            0,
            0,
            tzinfo=APPLICATION_TIMEZONE,
        ),
    )


def test_list_available_slots_converts_utc_reservation_to_local_time() -> None:
    """
    Verifica la conversion de una reserva UTC a la hora local.

    Una reserva a las 12:00 UTC representa las 09:00 en Buenos Aires.
    """
    service, sports_repository, reservation_repository = create_service()

    sports_repository.get_by_id.return_value = create_sports_space()

    reservation_repository.list_confirmed_for_space_between.return_value = [
        create_reservation(
            start_at=datetime(
                2026,
                11,
                3,
                12,
                0,
                tzinfo=UTC,
            ),
        ),
    ]

    slots = service.list_available_slots(
        sports_space_id=8,
        selected_date=date(2026, 11, 3),
    )

    assert [slot.start_at.hour for slot in slots] == [
        8,
        10,
        11,
    ]


def test_list_available_slots_returns_empty_when_no_complete_slot_fits() -> None:
    """
    Verifica el resultado cuando el horario no permite una hora completa.
    """
    service, sports_repository, reservation_repository = create_service()

    venue = create_venue(
        opening_time=time(8, 30),
        closing_time=time(9, 30),
    )
    sports_repository.get_by_id.return_value = create_sports_space(
        venue=venue,
    )
    reservation_repository.list_confirmed_for_space_between.return_value = []

    slots = service.list_available_slots(
        sports_space_id=8,
        selected_date=date(2026, 11, 3),
    )

    assert slots == []


def test_list_available_slots_rejects_naive_current_datetime() -> None:
    """
    Verifica que el reloj inyectado incluya zona horaria.
    """
    service, sports_repository, reservation_repository = create_service(
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
        service.list_available_slots(
            sports_space_id=8,
            selected_date=date(2026, 11, 3),
        )

    reservation_repository.list_confirmed_for_space_between.assert_not_called()
