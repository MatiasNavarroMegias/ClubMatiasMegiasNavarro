from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models import Reservation
from app.schemas import ReservationCreate, ReservationResponse


def test_reservation_create_accepts_datetime_with_timezone() -> None:
    """
    Verifica que la creacion acepte una fecha con zona horaria.

    El cliente movil enviara fechas con un desplazamiento explicito
    para evitar interpretaciones ambiguas entre sistemas.
    """
    reservation_data = ReservationCreate(
        sports_space_id=8,
        start_at="2026-11-02T18:00:00-03:00",
    )

    assert reservation_data.sports_space_id == 8
    assert reservation_data.start_at.year == 2026
    assert reservation_data.start_at.month == 11
    assert reservation_data.start_at.day == 2
    assert reservation_data.start_at.hour == 18
    assert reservation_data.start_at.minute == 0
    assert reservation_data.start_at.utcoffset() == timedelta(
        hours=-3,
    )


def test_reservation_create_accepts_utc_datetime() -> None:
    """
    Verifica que una fecha expresada en UTC tambien sea valida.
    """
    reservation_data = ReservationCreate(
        sports_space_id=8,
        start_at="2026-11-02T21:00:00Z",
    )

    assert reservation_data.start_at == datetime(
        2026,
        11,
        2,
        21,
        0,
        tzinfo=UTC,
    )


def test_reservation_create_rejects_datetime_without_timezone() -> None:
    """
    Verifica que una fecha sin zona horaria sea rechazada.
    """
    with pytest.raises(
        ValidationError,
        match="La fecha de inicio debe incluir una zona horaria",
    ):
        ReservationCreate(
            sports_space_id=8,
            start_at="2026-11-02T18:00:00",
        )


def test_reservation_create_rejects_invalid_sports_space_id() -> None:
    """
    Verifica que el identificador del espacio sea mayor que cero.
    """
    with pytest.raises(ValidationError):
        ReservationCreate(
            sports_space_id=0,
            start_at="2026-11-02T18:00:00-03:00",
        )


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("id", 99),
        ("user_id", 5),
        ("end_at", "2026-11-02T19:00:00-03:00"),
        ("status", "confirmed"),
        ("cancelled_at", None),
        ("created_at", "2026-10-27T12:00:00Z"),
        ("updated_at", "2026-10-27T12:00:00Z"),
    ],
)
def test_reservation_create_rejects_protected_fields(
    field_name: str,
    field_value: object,
) -> None:
    """
    Verifica que el cliente no pueda enviar campos internos.

    El usuario, la finalizacion, el estado y las fechas de auditoria
    seran administrados exclusivamente por el backend.
    """
    payload = {
        "sports_space_id": 8,
        "start_at": "2026-11-02T18:00:00-03:00",
        field_name: field_value,
    }

    with pytest.raises(
        ValidationError,
        match="Extra inputs are not permitted",
    ):
        ReservationCreate.model_validate(payload)


def test_reservation_response_can_be_created_from_confirmed_model() -> None:
    """
    Verifica una respuesta creada desde una reserva confirmada.
    """
    start_at = datetime(
        2026,
        11,
        2,
        18,
        0,
        tzinfo=UTC,
    )
    end_at = start_at + timedelta(hours=1)
    audit_time = datetime(
        2026,
        10,
        27,
        12,
        0,
        tzinfo=UTC,
    )

    reservation = Reservation(
        id=1,
        user_id=5,
        sports_space_id=8,
        start_at=start_at,
        end_at=end_at,
        status="confirmed",
        cancelled_at=None,
        created_at=audit_time,
        updated_at=audit_time,
    )

    response = ReservationResponse.model_validate(
        reservation,
    )

    assert response.id == 1
    assert response.user_id == 5
    assert response.sports_space_id == 8
    assert response.start_at == start_at
    assert response.end_at == end_at
    assert response.status == "confirmed"
    assert response.cancelled_at is None
    assert response.created_at == audit_time
    assert response.updated_at == audit_time


def test_reservation_response_can_be_created_from_cancelled_model() -> None:
    """
    Verifica que la respuesta preserve una cancelacion logica.
    """
    start_at = datetime(
        2026,
        11,
        2,
        18,
        0,
        tzinfo=UTC,
    )
    cancellation_time = datetime(
        2026,
        10,
        30,
        10,
        15,
        tzinfo=UTC,
    )
    creation_time = datetime(
        2026,
        10,
        27,
        12,
        0,
        tzinfo=UTC,
    )

    reservation = Reservation(
        id=2,
        user_id=5,
        sports_space_id=8,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
        status="cancelled",
        cancelled_at=cancellation_time,
        created_at=creation_time,
        updated_at=cancellation_time,
    )

    response = ReservationResponse.model_validate(
        reservation,
    )

    assert response.id == 2
    assert response.status == "cancelled"
    assert response.cancelled_at == cancellation_time
    assert response.updated_at == cancellation_time


def test_reservation_response_contains_expected_fields() -> None:
    """
    Verifica los campos publicados por la respuesta.
    """
    response_fields = set(
        ReservationResponse.model_fields,
    )

    assert response_fields == {
        "id",
        "user_id",
        "sports_space_id",
        "start_at",
        "end_at",
        "status",
        "cancelled_at",
        "created_at",
        "updated_at",
    }
