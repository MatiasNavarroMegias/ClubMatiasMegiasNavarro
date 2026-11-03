from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_auth_service
from app.core.security import AccessTokenService, PasswordHasher
from app.main import app
from app.models import User
from app.repositories import UserRepository
from app.services import (
    AuthService,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
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


def valid_login_json() -> dict:
    """
    Devuelve credenciales validas reutilizables para las pruebas.
    """
    return {
        "email": "matias@example.com",
        "password": "ClaveSegura123",
    }


@pytest.fixture
def auth_api() -> tuple[TestClient, MagicMock]:
    """
    Crea un cliente HTTP conectado con un servicio simulado.

    dependency_overrides evita utilizar PostgreSQL, ejecutar Argon2
    o generar tokens JWT reales durante las pruebas de la capa HTTP.
    """
    service = MagicMock(spec=AuthService)

    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)

    return client, service


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """
    Limpia las dependencias reemplazadas despues de cada prueba.

    Esto evita que una dependencia simulada afecte otras pruebas.
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
    assert isinstance(
        service.access_token_service,
        AccessTokenService,
    )
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


def test_login_user_returns_token_for_valid_credentials(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que las credenciales validas produzcan un token bearer.
    """
    client, service = auth_api
    service.login_user.return_value = "signed-access-token"

    response = client.post(
        "/auth/login",
        json=valid_login_json(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "signed-access-token",
        "token_type": "bearer",
    }

    service.login_user.assert_called_once()


def test_login_user_receives_normalized_email(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que Pydantic normalice el correo antes del servicio.
    """
    client, service = auth_api
    service.login_user.return_value = "signed-access-token"

    response = client.post(
        "/auth/login",
        json={
            "email": "MATIAS@EXAMPLE.COM",
            "password": "ClaveSegura123",
        },
    )

    assert response.status_code == 200

    login_data = service.login_user.call_args.args[0]

    assert login_data.email == "matias@example.com"
    assert login_data.password == "ClaveSegura123"


def test_login_user_returns_401_for_invalid_credentials(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica la respuesta ante credenciales incorrectas.
    """
    client, service = auth_api
    service.login_user.side_effect = InvalidCredentialsError("Correo o contrasena incorrectos.")

    response = client.post(
        "/auth/login",
        json=valid_login_json(),
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Correo o contrasena incorrectos.",
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_user_returns_same_error_for_unknown_email(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que la API no revele si un correo esta registrado.
    """
    client, service = auth_api
    service.login_user.side_effect = InvalidCredentialsError("Correo o contrasena incorrectos.")

    response = client.post(
        "/auth/login",
        json={
            "email": "desconocido@example.com",
            "password": "ClaveSegura123",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Correo o contrasena incorrectos.",
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_user_returns_403_for_inactive_account(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que una cuenta inactiva no pueda iniciar sesion.
    """
    client, service = auth_api
    service.login_user.side_effect = InactiveUserError(
        "La cuenta de usuario se encuentra inactiva."
    )

    response = client.post(
        "/auth/login",
        json=valid_login_json(),
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "La cuenta de usuario se encuentra inactiva.",
    }


def test_login_user_returns_422_for_invalid_email(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que un correo invalido se rechace antes del servicio.
    """
    client, service = auth_api

    response = client.post(
        "/auth/login",
        json={
            "email": "correo-invalido",
            "password": "ClaveSegura123",
        },
    )

    assert response.status_code == 422
    service.login_user.assert_not_called()


def test_login_user_returns_422_for_empty_password(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que una contrasena vacia se rechace antes del servicio.
    """
    client, service = auth_api

    response = client.post(
        "/auth/login",
        json={
            "email": "matias@example.com",
            "password": "",
        },
    )

    assert response.status_code == 422
    service.login_user.assert_not_called()


def test_login_response_does_not_expose_private_data(
    auth_api: tuple[TestClient, MagicMock],
) -> None:
    """
    Verifica que la respuesta contenga solamente informacion del token.
    """
    client, service = auth_api
    service.login_user.return_value = "signed-access-token"

    response = client.post(
        "/auth/login",
        json=valid_login_json(),
    )

    response_data = response.json()

    assert response_data == {
        "access_token": "signed-access-token",
        "token_type": "bearer",
    }

    assert "password" not in response_data
    assert "password_hash" not in response_data
    assert "email" not in response_data
    assert "user_id" not in response_data
