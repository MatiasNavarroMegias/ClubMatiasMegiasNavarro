from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_reservation_service,
)
from app.main import app
from app.models import Reservation, User
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


def create_user(
    *,
    user_id: int = 7,
) -> User:
    """
    Construye un usuario autenticado para las pruebas HTTP.

    El objeto se crea en memoria y no se guarda en PostgreSQL.
    """
    audit_time = datetime(
        2026,
        10,
        27,
        12,
        0,
        tzinfo=UTC,
    )

    return User(
        id=user_id,
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(
            2000,
            1,
            15,
        ),
        email="matias@example.com",
        password_hash="$argon2id$hash-de-prueba",
        is_active=True,
        created_at=audit_time,
        updated_at=audit_time,
    )


def create_reservation(
    *,
    reservation_id: int = 1,
    user_id: int = 7,
    sports_space_id: int = 8,
    start_at: datetime | None = None,
) -> Reservation:
    """
    Construye una reserva confirmada para las pruebas del endpoint.
    """
    reservation_start = start_at or datetime(
        2026,
        11,
        3,
        18,
        0,
        tzinfo=APPLICATION_TIMEZONE,
    )
    audit_time = datetime(
        2026,
        10,
        27,
        12,
        0,
        tzinfo=UTC,
    )

    return Reservation(
        id=reservation_id,
        user_id=user_id,
        sports_space_id=sports_space_id,
        start_at=reservation_start,
        end_at=reservation_start + timedelta(hours=1),
        status="confirmed",
        cancelled_at=None,
        created_at=audit_time,
        updated_at=audit_time,
    )


def valid_reservation_json() -> dict:
    """
    Devuelve un cuerpo JSON valido para crear una reserva.
    """
    return {
        "sports_space_id": 8,
        "start_at": "2026-11-03T18:00:00-03:00",
    }


@pytest.fixture
def reservation_api() -> tuple[
    TestClient,
    MagicMock,
    User,
]:
    """
    Crea un cliente HTTP con servicio y usuario simulados.

    Los reemplazos evitan utilizar PostgreSQL y tokens JWT reales
    durante las pruebas funcionales del endpoint.
    """
    service = MagicMock(
        spec=ReservationService,
    )
    current_user = create_user()

    app.dependency_overrides[get_reservation_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: current_user

    client = TestClient(app)

    return client, service, current_user


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """
    Limpia las dependencias reemplazadas despues de cada prueba.
    """
    yield

    app.dependency_overrides.clear()


def test_get_reservation_service_builds_dependencies() -> None:
    """
    Verifica la construccion real del servicio y sus repositorios.
    """
    database_session = MagicMock(
        spec=Session,
    )

    service = get_reservation_service(
        database_session,
    )

    assert isinstance(
        service,
        ReservationService,
    )
    assert service.reservation_repository.database_session is database_session
    assert service.sports_space_repository.database_session is database_session
    assert service.timezone.key == "America/Argentina/Buenos_Aires"


def test_create_reservation_returns_201(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica la creacion exitosa de una reserva.
    """
    client, service, current_user = reservation_api

    service.create_reservation.return_value = create_reservation(
        user_id=current_user.id,
    )

    response = client.post(
        "/reservations",
        json=valid_reservation_json(),
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["user_id"] == 7
    assert response.json()["sports_space_id"] == 8
    assert response.json()["status"] == "confirmed"
    assert response.json()["cancelled_at"] is None
    assert response.json()["start_at"] == "2026-11-03T18:00:00-03:00"
    assert response.json()["end_at"] == "2026-11-03T19:00:00-03:00"


def test_create_reservation_uses_authenticated_user(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica que el usuario provenga de la autenticacion.
    """
    client, service, current_user = reservation_api

    service.create_reservation.return_value = create_reservation(
        user_id=current_user.id,
    )

    response = client.post(
        "/reservations",
        json=valid_reservation_json(),
    )

    assert response.status_code == 201

    call_arguments = service.create_reservation.call_args.kwargs

    assert call_arguments["user_id"] == current_user.id

    reservation_data = call_arguments["reservation_data"]

    assert reservation_data.sports_space_id == 8
    assert reservation_data.start_at == datetime(
        2026,
        11,
        3,
        18,
        0,
        tzinfo=reservation_data.start_at.tzinfo,
    )
    assert reservation_data.start_at.utcoffset() == timedelta(
        hours=-3,
    )


def test_create_reservation_requires_bearer_token() -> None:
    """
    Verifica que el endpoint requiera autenticacion Bearer.

    En esta prueba solamente se reemplaza el servicio. La dependencia
    real de usuario permanece activa para comprobar la seguridad.
    """
    service = MagicMock(
        spec=ReservationService,
    )

    app.dependency_overrides[get_reservation_service] = lambda: service

    client = TestClient(app)

    response = client.post(
        "/reservations",
        json=valid_reservation_json(),
    )

    assert response.status_code in {
        401,
        403,
    }
    service.create_reservation.assert_not_called()


def test_create_reservation_rejects_user_id_in_body(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica que el cliente no pueda elegir otro propietario.
    """
    client, service, _ = reservation_api

    payload = {
        **valid_reservation_json(),
        "user_id": 999,
    }

    response = client.post(
        "/reservations",
        json=payload,
    )

    assert response.status_code == 422
    service.create_reservation.assert_not_called()


def test_create_reservation_rejects_datetime_without_timezone(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica que la fecha de inicio incluya zona horaria.
    """
    client, service, _ = reservation_api

    response = client.post(
        "/reservations",
        json={
            "sports_space_id": 8,
            "start_at": "2026-11-03T18:00:00",
        },
    )

    assert response.status_code == 422
    service.create_reservation.assert_not_called()


def test_create_reservation_rejects_invalid_sports_space_id(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica que el identificador del espacio sea positivo.
    """
    client, service, _ = reservation_api

    response = client.post(
        "/reservations",
        json={
            "sports_space_id": 0,
            "start_at": "2026-11-03T18:00:00-03:00",
        },
    )

    assert response.status_code == 422
    service.create_reservation.assert_not_called()


def test_create_reservation_returns_404_for_missing_space(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica la respuesta para un espacio inexistente.
    """
    client, service, _ = reservation_api

    service.create_reservation.side_effect = ReservationSportsSpaceNotFoundError(
        "No existe un espacio deportivo con el identificador 999."
    )

    response = client.post(
        "/reservations",
        json={
            "sports_space_id": 999,
            "start_at": "2026-11-03T18:00:00-03:00",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": ("No existe un espacio deportivo con el identificador 999.")
    }


def test_create_reservation_returns_409_for_inactive_space(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica la respuesta para un espacio inactivo.
    """
    client, service, _ = reservation_api

    service.create_reservation.side_effect = ReservationSportsSpaceInactiveError(
        "El espacio deportivo se encuentra inactivo."
    )

    response = client.post(
        "/reservations",
        json=valid_reservation_json(),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ("El espacio deportivo se encuentra inactivo.")}


def test_create_reservation_returns_409_for_inactive_venue(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica la respuesta para una sede inactiva.
    """
    client, service, _ = reservation_api

    service.create_reservation.side_effect = ReservationVenueInactiveError(
        "La sede del espacio deportivo se encuentra inactiva."
    )

    response = client.post(
        "/reservations",
        json=valid_reservation_json(),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ("La sede del espacio deportivo se encuentra inactiva.")}


def test_create_reservation_returns_409_for_time_conflict(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica la respuesta cuando el turno ya esta ocupado.
    """
    client, service, _ = reservation_api

    service.create_reservation.side_effect = ReservationTimeConflictError(
        "El turno solicitado ya se encuentra reservado."
    )

    response = client.post(
        "/reservations",
        json=valid_reservation_json(),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ("El turno solicitado ya se encuentra reservado.")}


def test_create_reservation_returns_422_for_past_start(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica la respuesta para un horario pasado.
    """
    client, service, _ = reservation_api

    service.create_reservation.side_effect = ReservationStartInPastError(
        "El horario de la reserva debe pertenecer al futuro."
    )

    response = client.post(
        "/reservations",
        json=valid_reservation_json(),
    )

    assert response.status_code == 422
    assert response.json() == {"detail": ("El horario de la reserva debe pertenecer al futuro.")}


def test_create_reservation_returns_422_for_non_full_hour(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica la respuesta para una hora no completa.
    """
    client, service, _ = reservation_api

    service.create_reservation.side_effect = ReservationInvalidStartTimeError(
        "La reserva debe comenzar en una hora completa."
    )

    response = client.post(
        "/reservations",
        json={
            "sports_space_id": 8,
            "start_at": "2026-11-03T18:30:00-03:00",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": ("La reserva debe comenzar en una hora completa.")}


def test_create_reservation_returns_422_outside_venue_hours(
    reservation_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica la respuesta para un turno fuera del horario.
    """
    client, service, _ = reservation_api

    service.create_reservation.side_effect = ReservationOutsideVenueHoursError(
        "El turno solicitado se encuentra fuera del horario de funcionamiento de la sede."
    )

    response = client.post(
        "/reservations",
        json={
            "sports_space_id": 8,
            "start_at": "2026-11-03T23:00:00-03:00",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "El turno solicitado se encuentra fuera del horario de funcionamiento de la sede."
        )
    }
