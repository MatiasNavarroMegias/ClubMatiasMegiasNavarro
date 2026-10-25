from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models import SportsSpace
from app.repositories import SportsSpaceRepository


def create_sports_space(
    *,
    space_id: int = 1,
    venue_id: int = 7,
    name: str = "Cancha de Futbol 1",
    sport_type: str = "Futbol",
    space_number: int = 1,
    is_active: bool = True,
) -> SportsSpace:
    """
    Construye un espacio deportivo reutilizable para las pruebas.

    El objeto no se guarda en PostgreSQL. Los valores pueden
    reemplazarse para representar diferentes resultados.
    """
    return SportsSpace(
        id=space_id,
        venue_id=venue_id,
        name=name,
        sport_type=sport_type,
        space_number=space_number,
        is_active=is_active,
    )


def test_list_all_returns_sports_spaces_from_session() -> None:
    """
    Verifica que list_all devuelva los espacios recibidos.

    La sesion simulada evita ejecutar consultas reales contra
    PostgreSQL.
    """
    database_session = MagicMock(spec=Session)

    expected_spaces = [
        create_sports_space(
            space_id=1,
            name="Cancha de Futbol 1",
            space_number=1,
        ),
        create_sports_space(
            space_id=2,
            name="Cancha de Futbol 2",
            space_number=2,
        ),
    ]

    database_session.scalars.return_value.all.return_value = expected_spaces

    repository = SportsSpaceRepository(database_session)

    spaces = repository.list_all()

    assert spaces == expected_spaces
    database_session.scalars.assert_called_once()


def test_list_all_builds_query_without_optional_filters() -> None:
    """
    Verifica que el listado general no agregue filtros innecesarios.
    """
    database_session = MagicMock(spec=Session)
    database_session.scalars.return_value.all.return_value = []

    repository = SportsSpaceRepository(database_session)

    repository.list_all()

    statement = database_session.scalars.call_args.args[0]
    compiled_statement = str(statement)

    assert "WHERE" not in compiled_statement
    assert "ORDER BY" in compiled_statement


def test_list_all_filters_by_venue() -> None:
    """
    Verifica el filtro de espacios pertenecientes a una sede.
    """
    database_session = MagicMock(spec=Session)
    database_session.scalars.return_value.all.return_value = []

    repository = SportsSpaceRepository(database_session)

    repository.list_all(
        venue_id=7,
    )

    statement = database_session.scalars.call_args.args[0]
    compiled_statement = str(statement)

    assert "sports_spaces.venue_id" in compiled_statement
    assert "WHERE" in compiled_statement

    compiled_parameters = statement.compile().params

    assert 7 in compiled_parameters.values()


def test_list_all_filters_by_sport_type() -> None:
    """
    Verifica el filtro por tipo de deporte.
    """
    database_session = MagicMock(spec=Session)
    database_session.scalars.return_value.all.return_value = []

    repository = SportsSpaceRepository(database_session)

    repository.list_all(
        sport_type="Tenis",
    )

    statement = database_session.scalars.call_args.args[0]
    compiled_statement = str(statement)

    assert "sports_spaces.sport_type" in compiled_statement

    compiled_parameters = statement.compile().params

    assert "Tenis" in compiled_parameters.values()


def test_list_all_filters_only_active_spaces() -> None:
    """
    Verifica que is_active excluya espacios inactivos.
    """
    database_session = MagicMock(spec=Session)
    database_session.scalars.return_value.all.return_value = []

    repository = SportsSpaceRepository(database_session)

    repository.list_all(
        is_active=True,
    )

    statement = database_session.scalars.call_args.args[0]
    compiled_statement = str(statement)

    assert "sports_spaces.is_active IS true" in compiled_statement


def test_list_all_combines_received_filters() -> None:
    """
    Verifica que sede, deporte y estado puedan combinarse.
    """
    database_session = MagicMock(spec=Session)
    database_session.scalars.return_value.all.return_value = []

    repository = SportsSpaceRepository(database_session)

    repository.list_all(
        venue_id=7,
        sport_type="Futbol",
        is_active=True,
    )

    statement = database_session.scalars.call_args.args[0]
    compiled_statement = str(statement)
    compiled_parameters = statement.compile().params

    assert "sports_spaces.venue_id" in compiled_statement
    assert "sports_spaces.sport_type" in compiled_statement
    assert "sports_spaces.is_active IS true" in compiled_statement

    assert 7 in compiled_parameters.values()
    assert "Futbol" in compiled_parameters.values()


def test_list_all_orders_spaces_by_sport_number_and_name() -> None:
    """
    Verifica el orden estable utilizado por la interfaz.
    """
    database_session = MagicMock(spec=Session)
    database_session.scalars.return_value.all.return_value = []

    repository = SportsSpaceRepository(database_session)

    repository.list_all()

    statement = database_session.scalars.call_args.args[0]
    compiled_statement = str(statement)

    assert "ORDER BY sports_spaces.sport_type" in compiled_statement
    assert "sports_spaces.space_number" in compiled_statement
    assert "sports_spaces.name" in compiled_statement


def test_get_by_id_returns_existing_sports_space() -> None:
    """
    Verifica la consulta mediante la clave primaria.
    """
    database_session = MagicMock(spec=Session)
    expected_space = create_sports_space()

    database_session.get.return_value = expected_space

    repository = SportsSpaceRepository(database_session)

    sports_space = repository.get_by_id(1)

    assert sports_space is expected_space
    database_session.get.assert_called_once_with(
        SportsSpace,
        1,
    )


def test_get_by_id_returns_none_when_space_does_not_exist() -> None:
    """
    Verifica que un identificador inexistente devuelva None.
    """
    database_session = MagicMock(spec=Session)
    database_session.get.return_value = None

    repository = SportsSpaceRepository(database_session)

    sports_space = repository.get_by_id(999)

    assert sports_space is None
    database_session.get.assert_called_once_with(
        SportsSpace,
        999,
    )


def test_get_by_identity_returns_existing_space() -> None:
    """
    Verifica la consulta por sede, deporte y numero.
    """
    database_session = MagicMock(spec=Session)
    expected_space = create_sports_space()

    database_session.scalar.return_value = expected_space

    repository = SportsSpaceRepository(database_session)

    sports_space = repository.get_by_identity(
        venue_id=7,
        sport_type="Futbol",
        space_number=1,
    )

    assert sports_space is expected_space
    database_session.scalar.assert_called_once()

    statement = database_session.scalar.call_args.args[0]
    compiled_statement = str(statement)
    compiled_parameters = statement.compile().params

    assert "sports_spaces.venue_id" in compiled_statement
    assert "sports_spaces.sport_type" in compiled_statement
    assert "sports_spaces.space_number" in compiled_statement

    assert 7 in compiled_parameters.values()
    assert "Futbol" in compiled_parameters.values()
    assert 1 in compiled_parameters.values()


def test_get_by_identity_returns_none_when_space_does_not_exist() -> None:
    """
    Verifica que una identidad inexistente devuelva None.
    """
    database_session = MagicMock(spec=Session)
    database_session.scalar.return_value = None

    repository = SportsSpaceRepository(database_session)

    sports_space = repository.get_by_identity(
        venue_id=7,
        sport_type="Tenis",
        space_number=99,
    )

    assert sports_space is None
    database_session.scalar.assert_called_once()


def test_add_persists_and_refreshes_sports_space() -> None:
    """
    Verifica que add agregue, confirme y recargue el modelo.
    """
    database_session = MagicMock(spec=Session)
    sports_space = create_sports_space()

    repository = SportsSpaceRepository(database_session)

    result = repository.add(sports_space)

    assert result is sports_space

    database_session.add.assert_called_once_with(
        sports_space,
    )
    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(
        sports_space,
    )


def test_save_commits_and_refreshes_existing_space() -> None:
    """
    Verifica la persistencia de un espacio previamente obtenido.
    """
    database_session = MagicMock(spec=Session)

    sports_space = create_sports_space(
        name="Cancha Renovada",
    )

    repository = SportsSpaceRepository(database_session)

    result = repository.save(sports_space)

    assert result is sports_space

    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(
        sports_space,
    )
    database_session.add.assert_not_called()


def test_list_all_filters_inactive_spaces() -> None:
    """
    Verifica que is_active=False filtre espacios inactivos.

    La comparacion explicita contra None evita confundir False con
    la ausencia del filtro.
    """
    database_session = MagicMock(spec=Session)
    database_session.scalars.return_value.all.return_value = []

    repository = SportsSpaceRepository(database_session)

    repository.list_all(
        is_active=False,
    )

    statement = database_session.scalars.call_args.args[0]
    compiled_statement = str(statement)

    assert "sports_spaces.is_active IS false" in compiled_statement
