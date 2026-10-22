from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_auth_service
from app.core.security import PasswordHasher
from app.main import app
from app.models import User
from app.repositories import UserRepository
from app.services import (
    AuthService,
    EmailAlreadyRegisteredError,
)


def create_user() -> User:
    """
    Crea un usuario reutilizable para las pruebas del endpoint.

    El objeto utiliza un hash ficticio y no se guarda en PostgreSQL.
    """
    audit_time = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)

    return User(
        id=1,
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email="matias@example.com",
        password_hash="$argon2id$hash-de-prueba",
        is_active=True,
        created_at=audit_time,
        updated_at=audit_time,
    )


def valid_registration_json() -> dict:
    """
    Devuelve un cuerpo JSON valido para registrar un usuario.
    """
    return {
        "first_name": "Matias",
        "last_name": "Megias Navarro",
        "birth_date": "2000-01-15",
        "email": "matias@example.com",
        "password": "ClaveSegura123",
    }


@pytest.fixture
def auth_api() -> tuple[TestClient, MagicMock]:
    """
    Crea un cliente HTTP conectado con un servicio simulado.

    dependency_overrides evita utilizar PostgreSQL y ejecutar Argon2
    durante las pruebas específicas de la capa HTTP.
    """
    service = MagicMock(spec=AuthService)

    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)

    return client, service


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """
    Limpia las dependencias reemplazadas despues de cada prueba.
    """
    yield
    app.dependency_overrides.clear()


def test_get_auth_service_builds_required_dependencies() -> None:
    """
    Verifica la construccion real de las dependencias de autenticacion.
    """
    database_session = MagicMock(spec=Session)

    service = get_auth_service(database_session)

    assert isinstance(service, AuthService)
    assert isinstance(service.repository, UserRepository)
    assert isinstance(service.password_hasher, PasswordHasher)
    assert service.repository.database_session is database_session


def test_register_user_returns_201_without_exposing_credentials(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica el registro exitoso y la estructura publica de la respuesta.
    """
    client, service = auth_api
    service.register_user.return_value = create_user()

    response = client.post(
        "/auth/register",
        json=valid_registration_json(),
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["id"] == 1
    assert response_data["first_name"] == "Matias"
    assert response_data["last_name"] == "Megias Navarro"
    assert response_data["birth_date"] == "2000-01-15"
    assert response_data["email"] == "matias@example.com"
    assert response_data["is_active"] is True

    assert "password" not in response_data
    assert "password_hash" not in response_data

    service.register_user.assert_called_once()


def test_register_user_receives_normalized_data(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que Pydantic normalice los datos antes del servicio.
    """
    client, service = auth_api
    service.register_user.return_value = create_user()

    response = client.post(
        "/auth/register",
        json={
            "first_name": " Matias ",
            "last_name": " Megias Navarro ",
            "birth_date": "2000-01-15",
            "email": "MATIAS@EXAMPLE.COM",
            "password": "ClaveSegura123",
        },
    )

    assert response.status_code == 201

    registration_data = service.register_user.call_args.args[0]

    assert registration_data.first_name == "Matias"
    assert registration_data.last_name == "Megias Navarro"
    assert registration_data.email == "matias@example.com"
    assert registration_data.password == "ClaveSegura123"


def test_register_user_returns_409_for_registered_email(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que un correo duplicado produzca una respuesta 409.
    """
    client, service = auth_api
    service.register_user.side_effect = EmailAlreadyRegisteredError(
        "Ya existe un usuario registrado con ese correo."
    )

    response = client.post(
        "/auth/register",
        json=valid_registration_json(),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Ya existe un usuario registrado con ese correo."}


def test_register_user_returns_422_for_invalid_password(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que una contrasena insegura se rechace antes del servicio.
    """
    client, service = auth_api
    registration_json = valid_registration_json()
    registration_json["password"] = "clavesegura"

    response = client.post(
        "/auth/register",
        json=registration_json,
    )

    assert response.status_code == 422
    service.register_user.assert_not_called()


def test_register_user_returns_422_for_invalid_email(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que un correo invalido se rechace antes del servicio.
    """
    client, service = auth_api
    registration_json = valid_registration_json()
    registration_json["email"] = "correo-invalido"

    response = client.post(
        "/auth/register",
        json=registration_json,
    )

    assert response.status_code == 422
    service.register_user.assert_not_called()


def test_register_user_returns_422_for_invalid_birth_date(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que una fecha futura se rechace antes del servicio.
    """
    client, service = auth_api
    registration_json = valid_registration_json()
    registration_json["birth_date"] = "2100-01-01"

    response = client.post(
        "/auth/register",
        json=registration_json,
    )

    assert response.status_code == 422
    service.register_user.assert_not_called()
