from datetime import date
from unittest.mock import MagicMock

from app.models import PushDevice, User
from app.repositories import PushDeviceRepository
from app.services import PushDeviceService


def create_user(
    user_id: int = 7,
) -> User:
    """
    Crea un usuario reutilizable para las pruebas del servicio.

    El objeto no se persiste y utiliza un hash ficticio.
    """
    return User(
        id=user_id,
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email=f"usuario{user_id}@example.com",
        password_hash="$argon2id$hash-de-prueba",
        is_active=True,
    )


def create_push_device(
    user_id: int = 7,
    platform: str = "android",
    is_active: bool = True,
) -> PushDevice:
    """
    Crea una instalacion reutilizable para las pruebas.

    El identificador representa un FID ficticio y no se conecta
    con Firebase.
    """
    return PushDevice(
        id=15,
        user_id=user_id,
        installation_id="firebase-installation-id-for-testing",
        platform=platform,
        is_active=is_active,
    )


def test_register_creates_device_when_installation_does_not_exist() -> None:
    """
    Verifica la creacion de una instalacion nueva.

    El usuario se obtiene desde la sesion autenticada y no desde
    informacion controlada por el cliente.
    """
    repository = MagicMock(spec=PushDeviceRepository)
    repository.get_by_installation_id.return_value = None
    repository.add.side_effect = lambda push_device: push_device

    service = PushDeviceService(repository)
    user = create_user()

    result = service.register(
        user=user,
        installation_id="new-firebase-installation-id",
        platform="android",
    )

    repository.get_by_installation_id.assert_called_once_with("new-firebase-installation-id")
    repository.add.assert_called_once()

    created_device = repository.add.call_args.args[0]

    assert result is created_device
    assert created_device.user_id == 7
    assert created_device.installation_id == "new-firebase-installation-id"
    assert created_device.platform == "android"
    assert created_device.is_active is True

    repository.save.assert_not_called()


def test_register_returns_device_without_saving_when_unchanged() -> None:
    """
    Verifica que una instalacion sin cambios no genere escritura.

    Evitar confirmaciones innecesarias reduce operaciones sobre
    PostgreSQL cuando Flutter repite el registro.
    """
    repository = MagicMock(spec=PushDeviceRepository)
    existing_device = create_push_device()

    repository.get_by_installation_id.return_value = existing_device

    service = PushDeviceService(repository)
    user = create_user()

    result = service.register(
        user=user,
        installation_id="firebase-installation-id-for-testing",
        platform="android",
    )

    assert result is existing_device
    repository.add.assert_not_called()
    repository.save.assert_not_called()


def test_register_reactivates_inactive_device() -> None:
    """
    Verifica que una instalacion inactiva pueda volver a utilizarse.
    """
    repository = MagicMock(spec=PushDeviceRepository)
    existing_device = create_push_device(
        is_active=False,
    )

    repository.get_by_installation_id.return_value = existing_device
    repository.save.side_effect = lambda push_device: push_device

    service = PushDeviceService(repository)
    user = create_user()

    result = service.register(
        user=user,
        installation_id="firebase-installation-id-for-testing",
        platform="android",
    )

    assert result is existing_device
    assert existing_device.is_active is True

    repository.add.assert_not_called()
    repository.save.assert_called_once_with(existing_device)


def test_register_updates_platform_when_it_changes() -> None:
    """
    Verifica la actualizacion de la plataforma registrada.

    Esta regla mantiene sincronizada la informacion informada por
    la aplicacion.
    """
    repository = MagicMock(spec=PushDeviceRepository)
    existing_device = create_push_device(
        platform="web",
    )

    repository.get_by_installation_id.return_value = existing_device
    repository.save.side_effect = lambda push_device: push_device

    service = PushDeviceService(repository)
    user = create_user()

    result = service.register(
        user=user,
        installation_id="firebase-installation-id-for-testing",
        platform="android",
    )

    assert result is existing_device
    assert existing_device.platform == "android"

    repository.add.assert_not_called()
    repository.save.assert_called_once_with(existing_device)


def test_register_reassigns_device_to_authenticated_user() -> None:
    """
    Verifica la reasignacion cuando la instalacion cambia de cuenta.

    Un mismo dispositivo puede cerrar sesion e iniciar sesion con
    otro usuario sin crear un registro duplicado.
    """
    repository = MagicMock(spec=PushDeviceRepository)
    existing_device = create_push_device(
        user_id=3,
    )

    repository.get_by_installation_id.return_value = existing_device
    repository.save.side_effect = lambda push_device: push_device

    service = PushDeviceService(repository)
    authenticated_user = create_user(
        user_id=7,
    )

    result = service.register(
        user=authenticated_user,
        installation_id="firebase-installation-id-for-testing",
        platform="android",
    )

    assert result is existing_device
    assert existing_device.user_id == 7
    assert existing_device.is_active is True

    repository.add.assert_not_called()
    repository.save.assert_called_once_with(existing_device)


def test_register_applies_all_changes_with_one_save() -> None:
    """
    Verifica que varias modificaciones generen una sola persistencia.

    Una instalacion puede necesitar reasignacion, cambio de plataforma
    y reactivacion dentro de la misma operacion.
    """
    repository = MagicMock(spec=PushDeviceRepository)
    existing_device = create_push_device(
        user_id=3,
        platform="web",
        is_active=False,
    )

    repository.get_by_installation_id.return_value = existing_device
    repository.save.side_effect = lambda push_device: push_device

    service = PushDeviceService(repository)
    authenticated_user = create_user(
        user_id=7,
    )

    result = service.register(
        user=authenticated_user,
        installation_id="firebase-installation-id-for-testing",
        platform="android",
    )

    assert result is existing_device
    assert existing_device.user_id == 7
    assert existing_device.platform == "android"
    assert existing_device.is_active is True

    repository.add.assert_not_called()
    repository.save.assert_called_once_with(existing_device)
