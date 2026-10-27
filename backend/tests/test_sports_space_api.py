from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_sports_space_service
from app.main import app
from app.models import SportsSpace
from app.services import (
    SportsSpaceAlreadyExistsError,
    SportsSpaceNoChangesError,
    SportsSpaceNotFoundError,
    SportsSpaceService,
    SportsSpaceVenueInactiveError,
    SportsSpaceVenueNotFoundError,
)


def create_sports_space(
    *,
    sports_space_id: int = 1,
    venue_id: int = 7,
    name: str = "Cancha de Futbol 1",
    sport_type: str = "Futbol",
    space_number: int = 1,
    is_active: bool = True,
) -> SportsSpace:
    """
    Construye un espacio deportivo para las pruebas HTTP.

    El objeto se crea en memoria y no se guarda en PostgreSQL.
    """
    audit_time = datetime(
        2026,
        10,
        25,
        12,
        0,
        tzinfo=UTC,
    )

    return SportsSpace(
        id=sports_space_id,
        venue_id=venue_id,
        name=name,
        sport_type=sport_type,
        space_number=space_number,
        is_active=is_active,
        created_at=audit_time,
        updated_at=audit_time,
    )


@pytest.fixture
def sports_space_api() -> tuple[TestClient, MagicMock]:
    """
    Crea un cliente HTTP con un servicio simulado.

    La dependencia real se reemplaza para evitar conexiones a
    PostgreSQL durante las pruebas de los endpoints.
    """
    service = MagicMock(
        spec=SportsSpaceService,
    )

    app.dependency_overrides[get_sports_space_service] = lambda: service

    client = TestClient(app)

    return client, service


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """
    Limpia las dependencias reemplazadas despues de cada prueba.
    """
    yield

    app.dependency_overrides.clear()


def test_get_sports_space_service_builds_dependencies() -> None:
    """
    Verifica la construccion del servicio y sus repositorios.
    """
    database_session = MagicMock(
        spec=Session,
    )

    service = get_sports_space_service(
        database_session,
    )

    assert isinstance(
        service,
        SportsSpaceService,
    )
    assert service.repository.database_session is database_session
    assert service.venue_repository.database_session is database_session


def test_list_sports_spaces_returns_spaces(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica el listado general de espacios deportivos.
    """
    client, service = sports_space_api

    service.list_sports_spaces.return_value = [
        create_sports_space(
            sports_space_id=1,
            name="Cancha de Futbol 1",
            space_number=1,
        ),
        create_sports_space(
            sports_space_id=2,
            name="Cancha de Futbol 2",
            space_number=2,
        ),
    ]

    response = client.get(
        "/sports-spaces",
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == 1
    assert response.json()[1]["id"] == 2
    assert response.json()[0]["name"] == "Cancha de Futbol 1"

    service.list_sports_spaces.assert_called_once_with(
        venue_id=None,
        sport_type=None,
        is_active=None,
    )


def test_list_sports_spaces_forwards_filters(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que los filtros lleguen al servicio.
    """
    client, service = sports_space_api
    service.list_sports_spaces.return_value = []

    response = client.get(
        "/sports-spaces",
        params={
            "venue_id": 7,
            "sport_type": "futbol",
            "is_active": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == []

    service.list_sports_spaces.assert_called_once_with(
        venue_id=7,
        sport_type="futbol",
        is_active=True,
    )


def test_list_sports_spaces_returns_422_for_invalid_venue_id(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que FastAPI rechace identificadores no positivos.
    """
    client, service = sports_space_api

    response = client.get(
        "/sports-spaces",
        params={
            "venue_id": 0,
        },
    )

    assert response.status_code == 422

    service.list_sports_spaces.assert_not_called()


def test_list_sports_spaces_returns_422_for_empty_sport_filter(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la traduccion de un filtro compuesto por espacios.
    """
    client, service = sports_space_api

    service.list_sports_spaces.side_effect = ValueError(
        "El tipo de deporte no puede contener solo espacios."
    )

    response = client.get(
        "/sports-spaces",
        params={
            "sport_type": "   ",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": ("El tipo de deporte no puede contener solo espacios.")}


def test_get_sports_space_returns_existing_space(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la consulta de un espacio existente.
    """
    client, service = sports_space_api

    service.get_sports_space.return_value = create_sports_space()

    response = client.get(
        "/sports-spaces/1",
    )

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["venue_id"] == 7
    assert response.json()["sport_type"] == "Futbol"
    assert response.json()["space_number"] == 1

    service.get_sports_space.assert_called_once_with(1)


def test_get_sports_space_returns_404_when_missing(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la respuesta para un espacio inexistente.
    """
    client, service = sports_space_api

    service.get_sports_space.side_effect = SportsSpaceNotFoundError(
        "No existe un espacio deportivo con el identificador 999."
    )

    response = client.get(
        "/sports-spaces/999",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": ("No existe un espacio deportivo con el identificador 999.")
    }


def test_create_sports_space_returns_201(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la creacion correcta de un espacio.
    """
    client, service = sports_space_api

    service.create_sports_space.return_value = create_sports_space()

    response = client.post(
        "/sports-spaces",
        json={
            "venue_id": 7,
            "name": "Cancha de Futbol 1",
            "sport_type": "futbol",
            "space_number": 1,
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["is_active"] is True

    sports_space_data = service.create_sports_space.call_args.args[0]

    assert sports_space_data.venue_id == 7
    assert sports_space_data.name == "Cancha de Futbol 1"
    assert sports_space_data.sport_type == "Futbol"
    assert sports_space_data.space_number == 1


def test_create_sports_space_returns_404_for_missing_venue(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la respuesta cuando la sede no existe.
    """
    client, service = sports_space_api

    service.create_sports_space.side_effect = SportsSpaceVenueNotFoundError(
        "No existe una sede con el identificador 999."
    )

    response = client.post(
        "/sports-spaces",
        json={
            "venue_id": 999,
            "name": "Cancha de Futbol 1",
            "sport_type": "Futbol",
            "space_number": 1,
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": ("No existe una sede con el identificador 999.")}


def test_create_sports_space_returns_409_for_inactive_venue(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la respuesta cuando la sede esta inactiva.
    """
    client, service = sports_space_api

    service.create_sports_space.side_effect = SportsSpaceVenueInactiveError(
        "No se pueden agregar espacios deportivos a una sede inactiva."
    )

    response = client.post(
        "/sports-spaces",
        json={
            "venue_id": 7,
            "name": "Cancha de Futbol 1",
            "sport_type": "Futbol",
            "space_number": 1,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": ("No se pueden agregar espacios deportivos a una sede inactiva.")
    }


def test_create_sports_space_returns_409_for_duplicate(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la respuesta para una identidad duplicada.
    """
    client, service = sports_space_api

    service.create_sports_space.side_effect = SportsSpaceAlreadyExistsError(
        "Ya existe un espacio deportivo con ese deporte y numero dentro de la sede."
    )

    response = client.post(
        "/sports-spaces",
        json={
            "venue_id": 7,
            "name": "Otra cancha",
            "sport_type": "Futbol",
            "space_number": 1,
        },
    )

    assert response.status_code == 409


def test_create_sports_space_returns_422_for_invalid_input(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que Pydantic rechace numeros no positivos.
    """
    client, service = sports_space_api

    response = client.post(
        "/sports-spaces",
        json={
            "venue_id": 7,
            "name": "Cancha de Futbol",
            "sport_type": "Futbol",
            "space_number": 0,
        },
    )

    assert response.status_code == 422
    service.create_sports_space.assert_not_called()


def test_update_sports_space_returns_updated_space(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la actualizacion correcta de un espacio.
    """
    client, service = sports_space_api

    service.update_sports_space.return_value = create_sports_space(
        name="Cancha Principal",
        is_active=False,
    )

    response = client.patch(
        "/sports-spaces/1",
        json={
            "name": "Cancha Principal",
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Cancha Principal"
    assert response.json()["is_active"] is False

    call_arguments = service.update_sports_space.call_args.kwargs

    assert call_arguments["sports_space_id"] == 1
    assert call_arguments["sports_space_data"].name == "Cancha Principal"
    assert call_arguments["sports_space_data"].is_active is False


def test_update_sports_space_returns_404_when_missing(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la actualizacion de un espacio inexistente.
    """
    client, service = sports_space_api

    service.update_sports_space.side_effect = SportsSpaceNotFoundError(
        "No existe un espacio deportivo con el identificador 999."
    )

    response = client.patch(
        "/sports-spaces/999",
        json={
            "name": "Cancha Principal",
        },
    )

    assert response.status_code == 404


def test_update_sports_space_returns_400_without_changes(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la respuesta para una solicitud vacia.
    """
    client, service = sports_space_api

    service.update_sports_space.side_effect = SportsSpaceNoChangesError(
        "La solicitud no contiene campos para modificar."
    )

    response = client.patch(
        "/sports-spaces/1",
        json={},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": ("La solicitud no contiene campos para modificar.")}


def test_update_sports_space_returns_409_for_duplicate(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica una identidad final duplicada.
    """
    client, service = sports_space_api

    service.update_sports_space.side_effect = SportsSpaceAlreadyExistsError(
        "Ya existe un espacio deportivo con ese deporte y numero dentro de la sede."
    )

    response = client.patch(
        "/sports-spaces/1",
        json={
            "sport_type": "Tenis",
            "space_number": 2,
        },
    )

    assert response.status_code == 409


def test_update_sports_space_rejects_venue_change(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que venue_id no pueda modificarse.
    """
    client, service = sports_space_api

    response = client.patch(
        "/sports-spaces/1",
        json={
            "venue_id": 20,
        },
    )

    assert response.status_code == 422
    service.update_sports_space.assert_not_called()


def test_list_sports_spaces_forwards_inactive_filter(
    sports_space_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que is_active=false llegue al servicio como False.
    """
    client, service = sports_space_api
    service.list_sports_spaces.return_value = []

    response = client.get(
        "/sports-spaces",
        params={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == []

    service.list_sports_spaces.assert_called_once_with(
        venue_id=None,
        sport_type=None,
        is_active=False,
    )
