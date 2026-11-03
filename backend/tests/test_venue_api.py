from datetime import UTC, datetime, time
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_venue_service
from app.main import app
from app.models import Venue
from app.services import (
    InvalidVenueHoursError,
    VenueNoChangesError,
    VenueNotFoundError,
    VenueService,
)


def create_venue(
    *,
    venue_id: int = 1,
    name: str = "Sede Ramos Mejia",
) -> Venue:
    """
    Crea una sede reutilizable para las pruebas de endpoints.

    La sede se construye como objeto Python y no se guarda dentro
    de PostgreSQL.
    """
    audit_time = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

    return Venue(
        id=venue_id,
        name=name,
        address="Avenida de Mayo 1000",
        opening_time=time(8, 0),
        closing_time=time(23, 0),
        is_active=True,
        created_at=audit_time,
        updated_at=audit_time,
    )


@pytest.fixture
def venue_api() -> tuple[TestClient, MagicMock]:
    """
    Crea un cliente HTTP conectado con un servicio simulado.

    dependency_overrides reemplaza temporalmente la construccion real
    de VenueService. De esta forma, las pruebas no utilizan PostgreSQL.
    """
    service = MagicMock(spec=VenueService)

    app.dependency_overrides[get_venue_service] = lambda: service
    client = TestClient(app)

    return client, service


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """
    Limpia las dependencias reemplazadas despues de cada prueba.

    Esta limpieza evita que una prueba modifique el comportamiento
    de las pruebas ejecutadas posteriormente.
    """
    yield
    app.dependency_overrides.clear()


def test_get_venue_service_builds_repository_and_service() -> None:
    """
    Verifica la construccion de las dependencias reales de sedes.

    La funcion recibe una sesion administrada por FastAPI, crea el
    repositorio y entrega un servicio preparado para los endpoints.
    """
    database_session = MagicMock(spec=Session)

    service = get_venue_service(database_session)

    assert isinstance(service, VenueService)
    assert service.repository.database_session is database_session


def test_list_venues_returns_venues(
    venue_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que GET /venues devuelva una lista de sedes.
    """
    client, service = venue_api
    service.list_venues.return_value = [
        create_venue(venue_id=1, name="Sede Moron"),
        create_venue(venue_id=2, name="Sede Ramos Mejia"),
    ]

    response = client.get("/venues")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Sede Moron"
    assert response.json()[1]["name"] == "Sede Ramos Mejia"
    service.list_venues.assert_called_once_with()


def test_get_venue_returns_existing_venue(
    venue_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que GET /venues/{venue_id} devuelva una sede existente.
    """
    client, service = venue_api
    service.get_venue.return_value = create_venue()

    response = client.get("/venues/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "Sede Ramos Mejia"
    service.get_venue.assert_called_once_with(1)


def test_get_venue_returns_404_when_venue_does_not_exist(
    venue_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que una sede inexistente produzca una respuesta 404.
    """
    client, service = venue_api
    service.get_venue.side_effect = VenueNotFoundError(
        "No existe una sede con el identificador 999."
    )

    response = client.get("/venues/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "No existe una sede con el identificador 999."}


def test_create_venue_returns_201(
    venue_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que POST /venues cree una sede y devuelva codigo 201.
    """
    client, service = venue_api
    service.create_venue.return_value = create_venue()

    response = client.post(
        "/venues",
        json={
            "name": "Sede Ramos Mejia",
            "address": "Avenida de Mayo 1000",
            "opening_time": "08:00:00",
            "closing_time": "23:00:00",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["is_active"] is True

    venue_data = service.create_venue.call_args.args[0]

    assert venue_data.name == "Sede Ramos Mejia"
    assert venue_data.opening_time == time(8, 0)


def test_create_venue_returns_422_for_invalid_input(
    venue_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que Pydantic rechace horarios invertidos antes del servicio.
    """
    client, service = venue_api

    response = client.post(
        "/venues",
        json={
            "name": "Sede Ramos Mejia",
            "address": "Avenida de Mayo 1000",
            "opening_time": "23:00:00",
            "closing_time": "08:00:00",
        },
    )

    assert response.status_code == 422
    service.create_venue.assert_not_called()


def test_update_venue_returns_updated_venue(
    venue_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que PATCH /venues/{venue_id} devuelva la sede actualizada.
    """
    client, service = venue_api
    service.update_venue.return_value = create_venue(name="Sede Ramos Mejia Centro")

    response = client.patch(
        "/venues/1",
        json={
            "name": "Sede Ramos Mejia Centro",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Sede Ramos Mejia Centro"

    venue_id = service.update_venue.call_args.kwargs["venue_id"]
    venue_data = service.update_venue.call_args.kwargs["venue_data"]

    assert venue_id == 1
    assert venue_data.name == "Sede Ramos Mejia Centro"


def test_update_venue_returns_404_when_venue_does_not_exist(
    venue_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que PATCH devuelva 404 cuando la sede no existe.
    """
    client, service = venue_api
    service.update_venue.side_effect = VenueNotFoundError(
        "No existe una sede con el identificador 999."
    )

    response = client.patch(
        "/venues/999",
        json={
            "name": "Nuevo nombre",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "No existe una sede con el identificador 999."}


def test_update_venue_returns_400_without_changes(
    venue_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que PATCH devuelva 400 cuando no existen cambios.
    """
    client, service = venue_api
    service.update_venue.side_effect = VenueNoChangesError(
        "La solicitud no contiene campos para modificar."
    )

    response = client.patch(
        "/venues/1",
        json={},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "La solicitud no contiene campos para modificar."}


def test_update_venue_returns_422_for_invalid_final_hours(
    venue_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que PATCH traduzca un horario invalido al codigo 422.
    """
    client, service = venue_api
    service.update_venue.side_effect = InvalidVenueHoursError(
        "El horario de cierre debe ser posterior al horario de apertura."
    )

    response = client.patch(
        "/venues/1",
        json={
            "closing_time": "07:00:00",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": ("El horario de cierre debe ser posterior al horario de apertura.")
    }
