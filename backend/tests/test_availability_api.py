from datetime import date, datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_availability_service
from app.main import app
from app.schemas import AvailabilitySlotResponse
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


@pytest.fixture
def availability_api() -> tuple[TestClient, MagicMock]:
    """
    Crea un cliente HTTP con un servicio de disponibilidad simulado.

    La dependencia real se reemplaza para evitar consultas a
    PostgreSQL durante las pruebas del endpoint.
    """
    service = MagicMock(
        spec=AvailabilityService,
    )

    app.dependency_overrides[get_availability_service] = lambda: service

    client = TestClient(app)

    return client, service


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """
    Limpia las dependencias reemplazadas despues de cada prueba.

    Esta limpieza evita que una prueba cambie el comportamiento de
    otras pruebas de la API.
    """
    yield

    app.dependency_overrides.clear()


def create_slot(
    *,
    start_hour: int,
) -> AvailabilitySlotResponse:
    """
    Construye un turno disponible de una hora.

    Args:
        start_hour: Hora local de inicio del turno.

    Returns:
        Turno disponible con zona horaria de Buenos Aires.
    """
    return AvailabilitySlotResponse(
        start_at=datetime(
            2026,
            11,
            3,
            start_hour,
            0,
            tzinfo=APPLICATION_TIMEZONE,
        ),
        end_at=datetime(
            2026,
            11,
            3,
            start_hour + 1,
            0,
            tzinfo=APPLICATION_TIMEZONE,
        ),
    )


def test_get_availability_service_builds_dependencies() -> None:
    """
    Verifica la construccion real del servicio de disponibilidad.
    """
    database_session = MagicMock(
        spec=Session,
    )

    service = get_availability_service(
        database_session,
    )

    assert isinstance(
        service,
        AvailabilityService,
    )
    assert service.sports_space_repository.database_session is database_session
    assert service.reservation_repository.database_session is database_session
    assert service.timezone.key == "America/Argentina/Buenos_Aires"


def test_list_availability_returns_available_slots(
    availability_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica una respuesta exitosa con turnos disponibles.
    """
    client, service = availability_api

    service.list_available_slots.return_value = [
        create_slot(
            start_hour=8,
        ),
        create_slot(
            start_hour=10,
        ),
    ]

    response = client.get(
        "/sports-spaces/8/availability",
        params={
            "date": "2026-11-03",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 2

    assert response.json()[0] == {
        "start_at": "2026-11-03T08:00:00-03:00",
        "end_at": "2026-11-03T09:00:00-03:00",
    }
    assert response.json()[1] == {
        "start_at": "2026-11-03T10:00:00-03:00",
        "end_at": "2026-11-03T11:00:00-03:00",
    }

    service.list_available_slots.assert_called_once_with(
        sports_space_id=8,
        selected_date=date(
            2026,
            11,
            3,
        ),
    )


def test_list_availability_returns_empty_list_without_slots(
    availability_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica una consulta valida sin horarios disponibles.
    """
    client, service = availability_api
    service.list_available_slots.return_value = []

    response = client.get(
        "/sports-spaces/8/availability",
        params={
            "date": "2026-11-03",
        },
    )

    assert response.status_code == 200
    assert response.json() == []

    service.list_available_slots.assert_called_once_with(
        sports_space_id=8,
        selected_date=date(
            2026,
            11,
            3,
        ),
    )


def test_list_availability_returns_422_without_date(
    availability_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que el parametro date sea obligatorio.
    """
    client, service = availability_api

    response = client.get(
        "/sports-spaces/8/availability",
    )

    assert response.status_code == 422
    service.list_available_slots.assert_not_called()


def test_list_availability_returns_422_for_invalid_date_format(
    availability_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que FastAPI rechace una fecha con formato invalido.
    """
    client, service = availability_api

    response = client.get(
        "/sports-spaces/8/availability",
        params={
            "date": "03-11-2026",
        },
    )

    assert response.status_code == 422
    service.list_available_slots.assert_not_called()


def test_list_availability_returns_404_for_missing_sports_space(
    availability_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la respuesta para un espacio inexistente.
    """
    client, service = availability_api

    service.list_available_slots.side_effect = AvailabilitySportsSpaceNotFoundError(
        "No existe un espacio deportivo con el identificador 999."
    )

    response = client.get(
        "/sports-spaces/999/availability",
        params={
            "date": "2026-11-03",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": ("No existe un espacio deportivo con el identificador 999.")
    }


def test_list_availability_returns_409_for_inactive_sports_space(
    availability_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la respuesta para un espacio inactivo.
    """
    client, service = availability_api

    service.list_available_slots.side_effect = AvailabilitySportsSpaceInactiveError(
        "El espacio deportivo se encuentra inactivo."
    )

    response = client.get(
        "/sports-spaces/8/availability",
        params={
            "date": "2026-11-03",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ("El espacio deportivo se encuentra inactivo.")}


def test_list_availability_returns_409_for_inactive_venue(
    availability_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la respuesta cuando la sede esta inactiva.
    """
    client, service = availability_api

    service.list_available_slots.side_effect = AvailabilityVenueInactiveError(
        "La sede del espacio deportivo se encuentra inactiva."
    )

    response = client.get(
        "/sports-spaces/8/availability",
        params={
            "date": "2026-11-03",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ("La sede del espacio deportivo se encuentra inactiva.")}


def test_list_availability_returns_422_for_past_date(
    availability_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la traduccion del error de fecha pasada.
    """
    client, service = availability_api

    service.list_available_slots.side_effect = AvailabilityDateInPastError(
        "No se puede consultar disponibilidad para una fecha pasada."
    )

    response = client.get(
        "/sports-spaces/8/availability",
        params={
            "date": "2026-10-20",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": ("No se puede consultar disponibilidad para una fecha pasada.")
    }


def test_list_availability_forwards_path_id_and_query_date(
    availability_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la conversion del ID y la fecha recibidos por HTTP.
    """
    client, service = availability_api
    service.list_available_slots.return_value = []

    response = client.get(
        "/sports-spaces/25/availability",
        params={
            "date": "2026-12-15",
        },
    )

    assert response.status_code == 200

    service.list_available_slots.assert_called_once_with(
        sports_space_id=25,
        selected_date=date(
            2026,
            12,
            15,
        ),
    )
