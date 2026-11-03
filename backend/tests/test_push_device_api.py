from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user,
    get_push_device_service,
)
from app.main import app
from app.models import PushDevice, User
from app.services import PushDeviceService


def create_user() -> User:
    """
    Construye un usuario autenticado reutilizable.

    El objeto no se persiste en PostgreSQL y utiliza un hash ficticio.
    """
    return User(
        id=7,
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email="matias@example.com",
        password_hash="$argon2id$hash-de-prueba",
        is_active=True,
    )


def create_push_device() -> PushDevice:
    """
    Construye una instalacion registrada reutilizable.

    Las fechas se definen manualmente porque la prueba no utiliza
    una base de datos real.
    """
    audit_time = datetime(
        2026,
        10,
        30,
        15,
        0,
        tzinfo=UTC,
    )

    return PushDevice(
        id=15,
        user_id=7,
        installation_id="firebase-installation-id",
        platform="android",
        is_active=True,
        created_at=audit_time,
        updated_at=audit_time,
    )


@pytest.fixture
def push_device_api() -> tuple[
    TestClient,
    User,
    MagicMock,
]:
    """
    Crea un cliente HTTP con usuario y servicio simulados.

    Las dependencias reemplazadas permiten probar la ruta sin consultar
    PostgreSQL ni validar un JWT real.
    """
    user = create_user()
    service = MagicMock(spec=PushDeviceService)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_push_device_service] = lambda: service

    client = TestClient(app)

    yield client, user, service

    app.dependency_overrides.clear()


def test_register_push_device_returns_registered_device(
    push_device_api: tuple[TestClient, User, MagicMock],
) -> None:
    """
    Verifica el registro exitoso de una instalacion push.
    """
    client, user, service = push_device_api
    registered_device = create_push_device()
    service.register.return_value = registered_device

    response = client.post(
        "/push-devices",
        headers={
            "Authorization": "Bearer token-de-prueba",
        },
        json={
            "installation_id": "firebase-installation-id",
            "platform": "android",
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["id"] == 15
    assert response_data["user_id"] == 7
    assert response_data["installation_id"] == ("firebase-installation-id")
    assert response_data["platform"] == "android"
    assert response_data["is_active"] is True
    assert "created_at" in response_data
    assert "updated_at" in response_data

    service.register.assert_called_once_with(
        user=user,
        installation_id="firebase-installation-id",
        platform="android",
    )


def test_register_push_device_normalizes_received_data(
    push_device_api: tuple[TestClient, User, MagicMock],
) -> None:
    """
    Verifica que la ruta utilice los datos normalizados por Pydantic.
    """
    client, user, service = push_device_api
    service.register.return_value = create_push_device()

    response = client.post(
        "/push-devices",
        headers={
            "Authorization": "Bearer token-de-prueba",
        },
        json={
            "installation_id": "  firebase-installation-id  ",
            "platform": "  ANDROID  ",
        },
    )

    assert response.status_code == 201

    service.register.assert_called_once_with(
        user=user,
        installation_id="firebase-installation-id",
        platform="android",
    )


def test_register_push_device_returns_422_for_invalid_platform(
    push_device_api: tuple[TestClient, User, MagicMock],
) -> None:
    """
    Verifica que una plataforma desconocida sea rechazada.
    """
    client, _, service = push_device_api

    response = client.post(
        "/push-devices",
        headers={
            "Authorization": "Bearer token-de-prueba",
        },
        json={
            "installation_id": "firebase-installation-id",
            "platform": "windows",
        },
    )

    assert response.status_code == 422
    service.register.assert_not_called()


def test_register_push_device_returns_422_for_extra_user_id(
    push_device_api: tuple[TestClient, User, MagicMock],
) -> None:
    """
    Verifica que el cliente no pueda seleccionar otro usuario.

    El usuario propietario se obtiene exclusivamente desde el JWT.
    """
    client, _, service = push_device_api

    response = client.post(
        "/push-devices",
        headers={
            "Authorization": "Bearer token-de-prueba",
        },
        json={
            "installation_id": "firebase-installation-id",
            "platform": "android",
            "user_id": 99,
        },
    )

    assert response.status_code == 422
    service.register.assert_not_called()


def test_register_push_device_returns_422_for_empty_id(
    push_device_api: tuple[TestClient, User, MagicMock],
) -> None:
    """
    Verifica que el identificador no pueda estar vacio.
    """
    client, _, service = push_device_api

    response = client.post(
        "/push-devices",
        headers={
            "Authorization": "Bearer token-de-prueba",
        },
        json={
            "installation_id": "   ",
            "platform": "android",
        },
    )

    assert response.status_code == 422
    service.register.assert_not_called()


def test_register_push_device_returns_401_without_token() -> None:
    """
    Verifica que el registro requiera una sesion autenticada.
    """
    app.dependency_overrides.clear()
    client = TestClient(app)

    response = client.post(
        "/push-devices",
        json={
            "installation_id": "firebase-installation-id",
            "platform": "android",
        },
    )

    assert response.status_code == 401
