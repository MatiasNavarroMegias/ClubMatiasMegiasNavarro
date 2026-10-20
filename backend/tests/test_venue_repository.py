from datetime import time
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models import Venue
from app.repositories import VenueRepository


def create_venue(name: str = "Sede Ramos Mejia") -> Venue:
    """
    Crea una sede reutilizable para las pruebas del repositorio.

    La funcion evita repetir la construccion del mismo objeto en cada
    prueba y no guarda informacion dentro de PostgreSQL.
    """
    return Venue(
        name=name,
        address="Avenida de Mayo 1000",
        opening_time=time(8, 0),
        closing_time=time(23, 0),
        is_active=True,
    )


def test_list_all_returns_venues_from_session() -> None:
    """
    Verifica que list_all devuelva las sedes obtenidas por la sesion.

    La prueba no ejecuta una consulta real. La cadena de objetos
    simulados representa el resultado producido por SQLAlchemy.
    """
    database_session = MagicMock(spec=Session)
    first_venue = create_venue("Sede Moron")
    second_venue = create_venue("Sede Ramos Mejia")
    expected_venues = [first_venue, second_venue]

    database_session.scalars.return_value.all.return_value = expected_venues

    repository = VenueRepository(database_session)

    venues = repository.list_all()

    assert venues == expected_venues
    database_session.scalars.assert_called_once()


def test_get_by_id_returns_venue_from_session() -> None:
    """
    Verifica que get_by_id busque una sede mediante su clave primaria.
    """
    database_session = MagicMock(spec=Session)
    expected_venue = create_venue()
    database_session.get.return_value = expected_venue

    repository = VenueRepository(database_session)

    venue = repository.get_by_id(1)

    assert venue is expected_venue
    database_session.get.assert_called_once_with(Venue, 1)


def test_get_by_id_returns_none_when_venue_does_not_exist() -> None:
    """
    Verifica que get_by_id devuelva None cuando la sede no existe.

    El repositorio no genera errores HTTP porque esa responsabilidad
    correspondera posteriormente al servicio o al endpoint.
    """
    database_session = MagicMock(spec=Session)
    database_session.get.return_value = None

    repository = VenueRepository(database_session)

    venue = repository.get_by_id(999)

    assert venue is None
    database_session.get.assert_called_once_with(Venue, 999)


def test_add_persists_and_refreshes_venue() -> None:
    """
    Verifica que add agregue, confirme y recargue una sede.

    refresh permite recuperar valores generados por PostgreSQL,
    como el identificador y las fechas de auditoria.
    """
    database_session = MagicMock(spec=Session)
    venue = create_venue()

    repository = VenueRepository(database_session)

    result = repository.add(venue)

    assert result is venue
    database_session.add.assert_called_once_with(venue)
    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(venue)


def test_save_commits_and_refreshes_existing_venue() -> None:
    """
    Verifica que save confirme y recargue una sede existente.

    No se llama nuevamente a add porque la instancia ya pertenece
    a la sesion que la obtuvo previamente.
    """
    database_session = MagicMock(spec=Session)
    venue = create_venue("Sede Actualizada")

    repository = VenueRepository(database_session)

    result = repository.save(venue)

    assert result is venue
    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(venue)
    database_session.add.assert_not_called()
