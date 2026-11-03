from unittest.mock import ANY, MagicMock

from sqlalchemy.orm import Session

from app.models import PushDevice
from app.repositories import PushDeviceRepository


def create_push_device(
    installation_id: str = "firebase-installation-id-for-testing",
) -> PushDevice:
    """
    Crea una instalacion reutilizable para las pruebas.

    El objeto no se persiste en PostgreSQL ni se conecta con Firebase.
    """
    return PushDevice(
        user_id=7,
        installation_id=installation_id,
        platform="android",
        is_active=True,
    )


def test_get_by_installation_id_returns_existing_device() -> None:
    """
    Verifica que el repositorio devuelva la instalacion encontrada.
    """
    database_session = MagicMock(spec=Session)
    expected_device = create_push_device()
    database_session.scalar.return_value = expected_device

    repository = PushDeviceRepository(database_session)

    device = repository.get_by_installation_id("firebase-installation-id-for-testing")

    assert device is expected_device
    database_session.scalar.assert_called_once_with(ANY)


def test_get_by_installation_id_builds_query_with_received_id() -> None:
    """
    Verifica que la consulta utilice el identificador recibido.

    La sentencia SQL se inspecciona sin ejecutar una consulta real
    contra PostgreSQL.
    """
    database_session = MagicMock(spec=Session)
    repository = PushDeviceRepository(database_session)

    repository.get_by_installation_id("firebase-installation-id-for-testing")

    statement = database_session.scalar.call_args.args[0]
    compiled_statement = statement.compile()
    query_parameters = compiled_statement.params

    assert "firebase-installation-id-for-testing" in query_parameters.values()


def test_get_by_installation_id_returns_none_when_not_found() -> None:
    """
    Verifica que una instalacion inexistente produzca None.

    El servicio decidira posteriormente si corresponde crear una
    instalacion nueva.
    """
    database_session = MagicMock(spec=Session)
    database_session.scalar.return_value = None

    repository = PushDeviceRepository(database_session)

    device = repository.get_by_installation_id("unknown-installation-id")

    assert device is None
    database_session.scalar.assert_called_once_with(ANY)


def test_add_persists_and_refreshes_device() -> None:
    """
    Verifica que add agregue, confirme y recargue la instalacion.
    """
    database_session = MagicMock(spec=Session)
    device = create_push_device()

    repository = PushDeviceRepository(database_session)

    result = repository.add(device)

    assert result is device
    database_session.add.assert_called_once_with(device)
    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(device)


def test_save_commits_and_refreshes_existing_device() -> None:
    """
    Verifica la persistencia de cambios sobre una instalacion existente.

    Esta operacion permitira reasignar, reactivar o desactivar una
    instalacion sin crear registros duplicados.
    """
    database_session = MagicMock(spec=Session)
    device = create_push_device()
    device.is_active = False

    repository = PushDeviceRepository(database_session)

    result = repository.save(device)

    assert result is device
    database_session.add.assert_not_called()
    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(device)
