from unittest.mock import MagicMock

import pytest

from app.models import SportsSpace, Venue
from app.repositories import SportsSpaceRepository, VenueRepository
from app.schemas import SportsSpaceCreate, SportsSpaceUpdate
from app.services import (
    SportsSpaceAlreadyExistsError,
    SportsSpaceNoChangesError,
    SportsSpaceNotFoundError,
    SportsSpaceService,
    SportsSpaceVenueInactiveError,
    SportsSpaceVenueNotFoundError,
)


def create_venue(
    *,
    venue_id: int = 7,
    is_active: bool = True,
) -> Venue:
    """
    Construye una sede reutilizable sin acceder a PostgreSQL.
    """
    return Venue(
        id=venue_id,
        name="Sede Ramos Mejia",
        address="Avenida de Mayo 1000",
        is_active=is_active,
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
    Construye un espacio deportivo reutilizable para las pruebas.
    """
    return SportsSpace(
        id=sports_space_id,
        venue_id=venue_id,
        name=name,
        sport_type=sport_type,
        space_number=space_number,
        is_active=is_active,
    )


def create_service() -> tuple[
    SportsSpaceService,
    MagicMock,
    MagicMock,
]:
    """
    Crea el servicio utilizando repositorios simulados.

    Los repositorios simulados permiten comprobar las reglas de
    negocio sin ejecutar consultas reales contra PostgreSQL.
    """
    repository = MagicMock(spec=SportsSpaceRepository)
    venue_repository = MagicMock(spec=VenueRepository)

    service = SportsSpaceService(
        repository=repository,
        venue_repository=venue_repository,
    )

    return service, repository, venue_repository


def test_list_sports_spaces_returns_repository_result() -> None:
    """
    Verifica el listado general sin filtros.
    """
    service, repository, _ = create_service()

    expected_spaces = [
        create_sports_space(
            sports_space_id=1,
            space_number=1,
        ),
        create_sports_space(
            sports_space_id=2,
            name="Cancha de Futbol 2",
            space_number=2,
        ),
    ]

    repository.list_all.return_value = expected_spaces

    spaces = service.list_sports_spaces()

    assert spaces == expected_spaces
    repository.list_all.assert_called_once_with(
        venue_id=None,
        sport_type=None,
        active_only=False,
    )


def test_list_sports_spaces_normalizes_and_combines_filters() -> None:
    """
    Verifica la normalizacion del deporte y los filtros combinados.
    """
    service, repository, _ = create_service()
    repository.list_all.return_value = []

    spaces = service.list_sports_spaces(
        venue_id=7,
        sport_type=" futbol ",
        active_only=True,
    )

    assert spaces == []
    repository.list_all.assert_called_once_with(
        venue_id=7,
        sport_type="Futbol",
        active_only=True,
    )


def test_list_sports_spaces_rejects_empty_sport_type() -> None:
    """
    Verifica que el filtro no pueda contener solamente espacios.
    """
    service, repository, _ = create_service()

    with pytest.raises(
        ValueError,
        match="no puede contener solo espacios",
    ):
        service.list_sports_spaces(
            sport_type="   ",
        )

    repository.list_all.assert_not_called()


def test_get_sports_space_returns_existing_space() -> None:
    """
    Verifica la consulta de un espacio existente.
    """
    service, repository, _ = create_service()
    expected_space = create_sports_space()

    repository.get_by_id.return_value = expected_space

    result = service.get_sports_space(1)

    assert result is expected_space
    repository.get_by_id.assert_called_once_with(1)


def test_get_sports_space_rejects_missing_space() -> None:
    """
    Verifica el error de dominio para un espacio inexistente.
    """
    service, repository, _ = create_service()
    repository.get_by_id.return_value = None

    with pytest.raises(
        SportsSpaceNotFoundError,
        match="identificador 999",
    ):
        service.get_sports_space(999)

    repository.get_by_id.assert_called_once_with(999)


def test_create_sports_space_builds_active_model_and_persists_it() -> None:
    """
    Verifica la creacion de un espacio dentro de una sede activa.
    """
    service, repository, venue_repository = create_service()

    venue_repository.get_by_id.return_value = create_venue()
    repository.get_by_identity.return_value = None
    repository.add.side_effect = lambda sports_space: sports_space

    create_data = SportsSpaceCreate(
        venue_id=7,
        name="Cancha de Futbol 1",
        sport_type="Futbol",
        space_number=1,
    )

    result = service.create_sports_space(create_data)

    assert result.venue_id == 7
    assert result.name == "Cancha de Futbol 1"
    assert result.sport_type == "Futbol"
    assert result.space_number == 1
    assert result.is_active is True

    venue_repository.get_by_id.assert_called_once_with(7)
    repository.get_by_identity.assert_called_once_with(
        venue_id=7,
        sport_type="Futbol",
        space_number=1,
    )
    repository.add.assert_called_once_with(result)


def test_create_sports_space_rejects_missing_venue() -> None:
    """
    Verifica que no pueda crearse un espacio sin una sede existente.
    """
    service, repository, venue_repository = create_service()
    venue_repository.get_by_id.return_value = None

    create_data = SportsSpaceCreate(
        venue_id=999,
        name="Cancha de Futbol 1",
        sport_type="Futbol",
        space_number=1,
    )

    with pytest.raises(
        SportsSpaceVenueNotFoundError,
        match="identificador 999",
    ):
        service.create_sports_space(create_data)

    venue_repository.get_by_id.assert_called_once_with(999)
    repository.get_by_identity.assert_not_called()
    repository.add.assert_not_called()


def test_create_sports_space_rejects_inactive_venue() -> None:
    """
    Verifica que una sede inactiva no reciba espacios nuevos.
    """
    service, repository, venue_repository = create_service()

    venue_repository.get_by_id.return_value = create_venue(
        is_active=False,
    )

    create_data = SportsSpaceCreate(
        venue_id=7,
        name="Cancha de Futbol 1",
        sport_type="Futbol",
        space_number=1,
    )

    with pytest.raises(
        SportsSpaceVenueInactiveError,
        match="sede inactiva",
    ):
        service.create_sports_space(create_data)

    repository.get_by_identity.assert_not_called()
    repository.add.assert_not_called()


def test_create_sports_space_rejects_duplicate_identity() -> None:
    """
    Verifica que no pueda repetirse la identidad de un espacio.
    """
    service, repository, venue_repository = create_service()

    venue_repository.get_by_id.return_value = create_venue()
    repository.get_by_identity.return_value = create_sports_space()

    create_data = SportsSpaceCreate(
        venue_id=7,
        name="Otra cancha",
        sport_type="Futbol",
        space_number=1,
    )

    with pytest.raises(
        SportsSpaceAlreadyExistsError,
        match="Ya existe un espacio deportivo",
    ):
        service.create_sports_space(create_data)

    repository.get_by_identity.assert_called_once_with(
        venue_id=7,
        sport_type="Futbol",
        space_number=1,
    )
    repository.add.assert_not_called()


def test_update_sports_space_applies_name_change() -> None:
    """
    Verifica una modificacion que no cambia la identidad.
    """
    service, repository, _ = create_service()

    existing_space = create_sports_space()
    repository.get_by_id.return_value = existing_space
    repository.save.side_effect = lambda sports_space: sports_space

    result = service.update_sports_space(
        1,
        SportsSpaceUpdate(
            name="Cancha Principal",
        ),
    )

    assert result.name == "Cancha Principal"
    assert result.sport_type == "Futbol"
    assert result.space_number == 1

    repository.get_by_identity.assert_not_called()
    repository.save.assert_called_once_with(existing_space)


def test_update_sports_space_rejects_empty_request() -> None:
    """
    Verifica que PATCH necesite al menos un campo.
    """
    service, repository, _ = create_service()
    repository.get_by_id.return_value = create_sports_space()

    with pytest.raises(
        SportsSpaceNoChangesError,
        match="no contiene campos para modificar",
    ):
        service.update_sports_space(
            1,
            SportsSpaceUpdate(),
        )

    repository.get_by_identity.assert_not_called()
    repository.save.assert_not_called()


def test_update_sports_space_rejects_unchanged_values() -> None:
    """
    Verifica que no se persistan valores iguales a los actuales.
    """
    service, repository, _ = create_service()
    repository.get_by_id.return_value = create_sports_space()

    update_data = SportsSpaceUpdate(
        name="Cancha de Futbol 1",
        sport_type="Futbol",
        space_number=1,
        is_active=True,
    )

    with pytest.raises(
        SportsSpaceNoChangesError,
        match="coinciden con los datos actuales",
    ):
        service.update_sports_space(
            1,
            update_data,
        )

    repository.get_by_identity.assert_not_called()
    repository.save.assert_not_called()


def test_update_sports_space_accepts_available_identity() -> None:
    """
    Verifica un cambio de deporte y numero sin una colision.
    """
    service, repository, _ = create_service()

    existing_space = create_sports_space()
    repository.get_by_id.return_value = existing_space
    repository.get_by_identity.return_value = None
    repository.save.side_effect = lambda sports_space: sports_space

    result = service.update_sports_space(
        1,
        SportsSpaceUpdate(
            name="Cancha de Tenis 2",
            sport_type="Tenis",
            space_number=2,
        ),
    )

    assert result.name == "Cancha de Tenis 2"
    assert result.sport_type == "Tenis"
    assert result.space_number == 2

    repository.get_by_identity.assert_called_once_with(
        venue_id=7,
        sport_type="Tenis",
        space_number=2,
    )
    repository.save.assert_called_once_with(existing_space)


def test_update_sports_space_rejects_duplicate_final_identity() -> None:
    """
    Verifica que la identidad final no pertenezca a otro espacio.
    """
    service, repository, _ = create_service()

    existing_space = create_sports_space(
        sports_space_id=1,
    )
    duplicate_space = create_sports_space(
        sports_space_id=2,
        sport_type="Tenis",
        space_number=2,
    )

    repository.get_by_id.return_value = existing_space
    repository.get_by_identity.return_value = duplicate_space

    with pytest.raises(
        SportsSpaceAlreadyExistsError,
        match="Ya existe un espacio deportivo",
    ):
        service.update_sports_space(
            1,
            SportsSpaceUpdate(
                sport_type="Tenis",
                space_number=2,
            ),
        )

    repository.get_by_identity.assert_called_once_with(
        venue_id=7,
        sport_type="Tenis",
        space_number=2,
    )
    repository.save.assert_not_called()


def test_update_sports_space_accepts_same_space_identity_result() -> None:
    """
    Verifica que el mismo espacio no sea considerado un duplicado.
    """
    service, repository, _ = create_service()

    existing_space = create_sports_space(
        sports_space_id=1,
    )

    repository.get_by_id.return_value = existing_space
    repository.get_by_identity.return_value = existing_space
    repository.save.side_effect = lambda sports_space: sports_space

    result = service.update_sports_space(
        1,
        SportsSpaceUpdate(
            sport_type="Tenis",
        ),
    )

    assert result.sport_type == "Tenis"
    repository.get_by_identity.assert_called_once_with(
        venue_id=7,
        sport_type="Tenis",
        space_number=1,
    )
    repository.save.assert_called_once_with(existing_space)


def test_update_sports_space_changes_active_status() -> None:
    """
    Verifica que el espacio pueda desactivarse sin eliminarse.
    """
    service, repository, _ = create_service()

    existing_space = create_sports_space(
        is_active=True,
    )

    repository.get_by_id.return_value = existing_space
    repository.save.side_effect = lambda sports_space: sports_space

    result = service.update_sports_space(
        1,
        SportsSpaceUpdate(
            is_active=False,
        ),
    )

    assert result.is_active is False
    repository.get_by_identity.assert_not_called()
    repository.save.assert_called_once_with(existing_space)
