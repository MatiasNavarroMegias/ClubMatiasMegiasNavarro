from datetime import time
from unittest.mock import MagicMock

import pytest

from app.models import Venue
from app.repositories import VenueRepository
from app.schemas import VenueCreate, VenueUpdate
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
    opening_time: time = time(8, 0),
    closing_time: time = time(23, 0),
) -> Venue:
    """
    Crea una sede reutilizable para las pruebas del servicio.

    La funcion construye un objeto de Python y no guarda datos
    dentro de PostgreSQL.
    """
    return Venue(
        id=venue_id,
        name=name,
        address="Avenida de Mayo 1000",
        opening_time=opening_time,
        closing_time=closing_time,
        is_active=True,
    )


def create_service() -> tuple[VenueService, MagicMock]:
    """
    Crea un servicio conectado con un repositorio simulado.

    El repositorio simulado permite comprobar reglas de negocio sin
    ejecutar consultas ni transacciones reales en PostgreSQL.
    """
    repository = MagicMock(spec=VenueRepository)
    service = VenueService(repository)

    return service, repository


def test_list_venues_returns_repository_result() -> None:
    """
    Verifica que el servicio devuelva las sedes del repositorio.
    """
    service, repository = create_service()
    expected_venues = [
        create_venue(venue_id=1, name="Sede Moron"),
        create_venue(venue_id=2, name="Sede Ramos Mejia"),
    ]
    repository.list_all.return_value = expected_venues

    venues = service.list_venues()

    assert venues == expected_venues
    repository.list_all.assert_called_once_with()


def test_get_venue_returns_existing_venue() -> None:
    """
    Verifica que el servicio devuelva una sede existente.
    """
    service, repository = create_service()
    expected_venue = create_venue()
    repository.get_by_id.return_value = expected_venue

    venue = service.get_venue(1)

    assert venue is expected_venue
    repository.get_by_id.assert_called_once_with(1)


def test_get_venue_raises_error_when_venue_does_not_exist() -> None:
    """
    Verifica que una sede inexistente produzca un error del dominio.

    El servicio no genera una excepcion HTTP porque no depende
    directamente de FastAPI.
    """
    service, repository = create_service()
    repository.get_by_id.return_value = None

    with pytest.raises(
        VenueNotFoundError,
        match="No existe una sede con el identificador 999",
    ):
        service.get_venue(999)

    repository.get_by_id.assert_called_once_with(999)


def test_create_venue_builds_active_model_and_persists_it() -> None:
    """
    Verifica que una sede nueva se cree activa y se persista.

    El identificador y las fechas seran generados posteriormente
    por PostgreSQL.
    """
    service, repository = create_service()
    venue_data = VenueCreate(
        name="Sede Ramos Mejia",
        address="Avenida de Mayo 1000",
        opening_time=time(8, 0),
        closing_time=time(23, 0),
    )
    repository.add.side_effect = lambda venue: venue

    venue = service.create_venue(venue_data)

    assert venue.name == "Sede Ramos Mejia"
    assert venue.address == "Avenida de Mayo 1000"
    assert venue.opening_time == time(8, 0)
    assert venue.closing_time == time(23, 0)
    assert venue.is_active is True
    repository.add.assert_called_once_with(venue)


def test_update_venue_applies_partial_change() -> None:
    """
    Verifica que el servicio modifique solamente los campos enviados.
    """
    service, repository = create_service()
    existing_venue = create_venue()
    repository.get_by_id.return_value = existing_venue
    repository.save.side_effect = lambda venue: venue

    update_data = VenueUpdate(name="Sede Ramos Mejia Centro")

    updated_venue = service.update_venue(1, update_data)

    assert updated_venue.name == "Sede Ramos Mejia Centro"
    assert updated_venue.address == "Avenida de Mayo 1000"
    assert updated_venue.opening_time == time(8, 0)
    assert updated_venue.closing_time == time(23, 0)
    repository.save.assert_called_once_with(existing_venue)


def test_update_venue_rejects_request_without_fields() -> None:
    """
    Verifica que una solicitud PATCH vacia no genere una transaccion.
    """
    service, repository = create_service()
    existing_venue = create_venue()
    repository.get_by_id.return_value = existing_venue

    with pytest.raises(
        VenueNoChangesError,
        match="La solicitud no contiene campos para modificar",
    ):
        service.update_venue(1, VenueUpdate())

    repository.save.assert_not_called()


def test_update_venue_rejects_values_equal_to_current_data() -> None:
    """
    Verifica que no se guarden valores iguales a los actuales.

    Esta regla evita confirmar una transaccion que no produce
    modificaciones reales.
    """
    service, repository = create_service()
    existing_venue = create_venue()
    repository.get_by_id.return_value = existing_venue

    update_data = VenueUpdate(
        name="Sede Ramos Mejia",
        opening_time=time(8, 0),
    )

    with pytest.raises(
        VenueNoChangesError,
        match="Los valores recibidos coinciden con los datos actuales",
    ):
        service.update_venue(1, update_data)

    repository.save.assert_not_called()


def test_update_venue_rejects_invalid_partial_hours() -> None:
    """
    Verifica el horario final cuando PATCH modifica solamente el cierre.

    VenueUpdate no puede validar por si solo este caso porque no conoce
    el horario de apertura almacenado en PostgreSQL.
    """
    service, repository = create_service()
    existing_venue = create_venue(
        opening_time=time(8, 0),
        closing_time=time(23, 0),
    )
    repository.get_by_id.return_value = existing_venue

    update_data = VenueUpdate(closing_time=time(7, 0))

    with pytest.raises(
        InvalidVenueHoursError,
        match="El horario de cierre debe ser posterior",
    ):
        service.update_venue(1, update_data)

    repository.save.assert_not_called()


def test_update_venue_accepts_valid_partial_hours() -> None:
    """
    Verifica una modificacion valida de un solo horario.

    El nuevo horario de apertura se combina con el cierre actual
    antes de realizar la validacion final.
    """
    service, repository = create_service()
    existing_venue = create_venue(
        opening_time=time(8, 0),
        closing_time=time(23, 0),
    )
    repository.get_by_id.return_value = existing_venue
    repository.save.side_effect = lambda venue: venue

    update_data = VenueUpdate(opening_time=time(9, 0))

    updated_venue = service.update_venue(1, update_data)

    assert updated_venue.opening_time == time(9, 0)
    assert updated_venue.closing_time == time(23, 0)
    repository.save.assert_called_once_with(existing_venue)
