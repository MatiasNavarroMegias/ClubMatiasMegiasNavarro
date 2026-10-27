from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user,
    get_reservation_service,
)
from app.main import app
from app.models import Reservation, User
from app.services import (
    ReservationAlreadyCancelledError,
    ReservationAlreadyStartedError,
    ReservationNotFoundError,
    ReservationService,
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
    status: str = "confirmed",
    cancelled_at: datetime | None = None,
) -> Reservation:
    """
    Construye una reserva reutilizable para las pruebas HTTP.
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
        status=status,
        cancelled_at=cancelled_at,
        created_at=audit_time,
        updated_at=cancelled_at or audit_time,
    )


@pytest.fixture
def reservation_lifecycle_api() -> tuple[
    TestClient,
    MagicMock,
    User,
]:
    """
    Crea un cliente HTTP con servicio y usuario simulados.

    Los reemplazos evitan utilizar PostgreSQL y tokens reales durante
    las pruebas de proximas reservas, historial y cancelacion.
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


def test_list_upcoming_reservations_returns_results(
    reservation_lifecycle_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica el listado de proximas reservas.
    """
    client, service, current_user = reservation_lifecycle_api

    service.list_upcoming_reservations.return_value = [
        create_reservation(
            reservation_id=1,
            user_id=current_user.id,
        ),
        create_reservation(
            reservation_id=2,
            user_id=current_user.id,
            start_at=datetime(
                2026,
                11,
                4,
                20,
                0,
                tzinfo=APPLICATION_TIMEZONE,
            ),
        ),
    ]

    response = client.get(
        "/reservations/upcoming",
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == 1
    assert response.json()[1]["id"] == 2
    assert response.json()[0]["status"] == "confirmed"
    assert response.json()[0]["cancelled_at"] is None

    service.list_upcoming_reservations.assert_called_once_with(
        user_id=current_user.id,
    )


def test_list_upcoming_reservations_returns_empty_list(
    reservation_lifecycle_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica una respuesta valida sin proximas reservas.
    """
    client, service, current_user = reservation_lifecycle_api
    service.list_upcoming_reservations.return_value = []

    response = client.get(
        "/reservations/upcoming",
    )

    assert response.status_code == 200
    assert response.json() == []

    service.list_upcoming_reservations.assert_called_once_with(
        user_id=current_user.id,
    )


def test_list_reservation_history_returns_finished_and_cancelled(
    reservation_lifecycle_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica el historial con reservas finalizadas y canceladas.
    """
    client, service, current_user = reservation_lifecycle_api

    cancellation_time = datetime(
        2026,
        11,
        1,
        12,
        0,
        tzinfo=APPLICATION_TIMEZONE,
    )

    service.list_reservation_history.return_value = [
        create_reservation(
            reservation_id=2,
            user_id=current_user.id,
            status="cancelled",
            cancelled_at=cancellation_time,
        ),
        create_reservation(
            reservation_id=1,
            user_id=current_user.id,
            start_at=datetime(
                2026,
                10,
                25,
                18,
                0,
                tzinfo=APPLICATION_TIMEZONE,
            ),
        ),
    ]

    response = client.get(
        "/reservations/history",
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["status"] == "cancelled"
    assert response.json()[0]["cancelled_at"] == "2026-11-01T12:00:00-03:00"
    assert response.json()[1]["status"] == "confirmed"

    service.list_reservation_history.assert_called_once_with(
        user_id=current_user.id,
    )


def test_list_reservation_history_returns_empty_list(
    reservation_lifecycle_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica una respuesta valida sin reservas historicas.
    """
    client, service, current_user = reservation_lifecycle_api
    service.list_reservation_history.return_value = []

    response = client.get(
        "/reservations/history",
    )

    assert response.status_code == 200
    assert response.json() == []

    service.list_reservation_history.assert_called_once_with(
        user_id=current_user.id,
    )


@pytest.mark.parametrize(
    "path",
    [
        "/reservations/upcoming",
        "/reservations/history",
        "/reservations/1/cancel",
    ],
)
def test_reservation_lifecycle_requires_authentication(
    path: str,
) -> None:
    """
    Verifica que los endpoints requieran autenticacion Bearer.
    """
    service = MagicMock(
        spec=ReservationService,
    )

    app.dependency_overrides[get_reservation_service] = lambda: service

    client = TestClient(app)

    if path.endswith("/cancel"):
        response = client.patch(path)
    else:
        response = client.get(path)

    assert response.status_code in {
        401,
        403,
    }

    service.list_upcoming_reservations.assert_not_called()
    service.list_reservation_history.assert_not_called()
    service.cancel_reservation.assert_not_called()


def test_cancel_reservation_returns_cancelled_reservation(
    reservation_lifecycle_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica una cancelacion correcta.
    """
    client, service, current_user = reservation_lifecycle_api

    cancellation_time = datetime(
        2026,
        11,
        2,
        10,
        30,
        tzinfo=APPLICATION_TIMEZONE,
    )

    service.cancel_reservation.return_value = create_reservation(
        reservation_id=5,
        user_id=current_user.id,
        status="cancelled",
        cancelled_at=cancellation_time,
    )

    response = client.patch(
        "/reservations/5/cancel",
    )

    assert response.status_code == 200
    assert response.json()["id"] == 5
    assert response.json()["user_id"] == current_user.id
    assert response.json()["status"] == "cancelled"
    assert response.json()["cancelled_at"] == "2026-11-02T10:30:00-03:00"

    service.cancel_reservation.assert_called_once_with(
        reservation_id=5,
        user_id=current_user.id,
    )


def test_cancel_reservation_returns_404_when_missing_or_foreign(
    reservation_lifecycle_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica una reserva inexistente o perteneciente a otro usuario.
    """
    client, service, current_user = reservation_lifecycle_api

    service.cancel_reservation.side_effect = ReservationNotFoundError(
        "No existe una reserva con el identificador 999 para el usuario autenticado."
    )

    response = client.patch(
        "/reservations/999/cancel",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": ("No existe una reserva con el identificador 999 para el usuario autenticado.")
    }

    service.cancel_reservation.assert_called_once_with(
        reservation_id=999,
        user_id=current_user.id,
    )


def test_cancel_reservation_returns_409_when_already_cancelled(
    reservation_lifecycle_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica el intento de cancelar nuevamente una reserva.
    """
    client, service, _ = reservation_lifecycle_api

    service.cancel_reservation.side_effect = ReservationAlreadyCancelledError(
        "La reserva ya se encuentra cancelada."
    )

    response = client.patch(
        "/reservations/1/cancel",
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "La reserva ya se encuentra cancelada."}


def test_cancel_reservation_returns_409_when_already_started(
    reservation_lifecycle_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica el intento de cancelar una reserva iniciada.
    """
    client, service, _ = reservation_lifecycle_api

    service.cancel_reservation.side_effect = ReservationAlreadyStartedError(
        "No se puede cancelar una reserva que ya comenzo."
    )

    response = client.patch(
        "/reservations/1/cancel",
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ("No se puede cancelar una reserva que ya comenzo.")}


def test_cancel_reservation_rejects_invalid_identifier(
    reservation_lifecycle_api: tuple[
        TestClient,
        MagicMock,
        User,
    ],
) -> None:
    """
    Verifica que FastAPI rechace un identificador no numerico.
    """
    client, service, _ = reservation_lifecycle_api

    response = client.patch(
        "/reservations/invalid/cancel",
    )

    assert response.status_code == 422
    service.cancel_reservation.assert_not_called()
