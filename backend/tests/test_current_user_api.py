from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.core.security import (
    AccessTokenService,
    InvalidAccessTokenError,
)
from app.main import app
from app.models import User

TEST_SECRET_KEY = "test-secret-key-with-at-least-32-characters"
TEST_ALGORITHM = "HS256"


def create_user(
    *,
    user_id: int = 7,
    is_active: bool = True,
) -> User:
    """
    Construye un usuario reutilizable para las pruebas.

    El objeto contiene un hash ficticio y no se persiste en PostgreSQL.
    """
    audit_time = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)

    return User(
        id=user_id,
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email="matias@example.com",
        password_hash="$argon2id$hash-de-prueba",
        is_active=is_active,
        created_at=audit_time,
        updated_at=audit_time,
    )


@pytest.fixture
def client() -> TestClient:
    """
    Crea un cliente HTTP y limpia reemplazos despues de cada prueba.
    """
    test_client = TestClient(app)

    yield test_client

    app.dependency_overrides.clear()


def test_get_current_user_returns_active_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica la dependencia con un token valido y una cuenta activa.
    """
    database_session = MagicMock(spec=Session)
    expected_user = create_user()
    database_session.get.return_value = expected_user

    token_service = AccessTokenService(
        secret_key=TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
        expire_minutes=60,
    )
    token = token_service.create_access_token(user_id=7)

    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("JWT_ALGORITHM", TEST_ALGORITHM)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    get_settings.cache_clear()

    credentials = MagicMock()
    credentials.credentials = token

    user = get_current_user(
        database_session=database_session,
        credentials=credentials,
    )

    assert user is expected_user
    database_session.get.assert_called_once_with(User, 7)

    get_settings.cache_clear()


def test_get_current_user_rejects_invalid_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que un token alterado produzca una respuesta 401.
    """
    database_session = MagicMock(spec=Session)

    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("JWT_ALGORITHM", TEST_ALGORITHM)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    get_settings.cache_clear()

    credentials = MagicMock()
    credentials.credentials = "invalid-token"

    with pytest.raises(HTTPException) as exception:
        get_current_user(
            database_session=database_session,
            credentials=credentials,
        )

    assert exception.value.status_code == 401
    assert exception.value.detail == "No se pudo validar la sesion."
    assert exception.value.headers == {
        "WWW-Authenticate": "Bearer",
    }

    database_session.get.assert_not_called()
    get_settings.cache_clear()


def test_get_current_user_rejects_expired_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que un token vencido produzca una respuesta 401.
    """
    database_session = MagicMock(spec=Session)

    token_service = AccessTokenService(
        secret_key=TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
        expire_minutes=60,
    )
    token = token_service.create_access_token(
        user_id=7,
        issued_at=datetime.now(UTC) - timedelta(hours=2),
    )

    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("JWT_ALGORITHM", TEST_ALGORITHM)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    get_settings.cache_clear()

    credentials = MagicMock()
    credentials.credentials = token

    with pytest.raises(HTTPException) as exception:
        get_current_user(
            database_session=database_session,
            credentials=credentials,
        )

    assert exception.value.status_code == 401
    assert exception.value.detail == "No se pudo validar la sesion."
    database_session.get.assert_not_called()

    get_settings.cache_clear()


def test_get_current_user_rejects_missing_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que un token de una cuenta inexistente produzca 401.
    """
    database_session = MagicMock(spec=Session)
    database_session.get.return_value = None

    token_service = AccessTokenService(
        secret_key=TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
        expire_minutes=60,
    )
    token = token_service.create_access_token(user_id=999)

    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("JWT_ALGORITHM", TEST_ALGORITHM)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    get_settings.cache_clear()

    credentials = MagicMock()
    credentials.credentials = token

    with pytest.raises(HTTPException) as exception:
        get_current_user(
            database_session=database_session,
            credentials=credentials,
        )

    assert exception.value.status_code == 401
    assert exception.value.detail == "No se pudo validar la sesion."
    assert exception.value.headers == {
        "WWW-Authenticate": "Bearer",
    }

    database_session.get.assert_called_once_with(User, 999)
    get_settings.cache_clear()


def test_get_current_user_rejects_inactive_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que una cuenta inactiva produzca una respuesta 403.
    """
    database_session = MagicMock(spec=Session)
    database_session.get.return_value = create_user(
        is_active=False,
    )

    token_service = AccessTokenService(
        secret_key=TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
        expire_minutes=60,
    )
    token = token_service.create_access_token(user_id=7)

    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("JWT_ALGORITHM", TEST_ALGORITHM)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    get_settings.cache_clear()

    credentials = MagicMock()
    credentials.credentials = token

    with pytest.raises(HTTPException) as exception:
        get_current_user(
            database_session=database_session,
            credentials=credentials,
        )

    assert exception.value.status_code == 403
    assert exception.value.detail == ("La cuenta de usuario se encuentra inactiva.")

    database_session.get.assert_called_once_with(User, 7)
    get_settings.cache_clear()


def test_get_my_profile_returns_authenticated_user(
    client: TestClient,
) -> None:
    """
    Verifica la respuesta publica del perfil autenticado.
    """
    expected_user = create_user()

    app.dependency_overrides[get_current_user] = lambda: expected_user

    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer token-de-prueba",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == 7
    assert response_data["first_name"] == "Matias"
    assert response_data["last_name"] == "Megias Navarro"
    assert response_data["birth_date"] == "2000-01-15"
    assert response_data["email"] == "matias@example.com"
    assert response_data["is_active"] is True

    assert "password" not in response_data
    assert "password_hash" not in response_data


def test_get_my_profile_returns_401_without_token(
    client: TestClient,
) -> None:
    """
    Verifica que el perfil requiera el encabezado Authorization.
    """
    response = client.get("/users/me")

    assert response.status_code == 401


def test_expired_token_payload_is_rejected() -> None:
    """
    Verifica adicionalmente la creacion controlada de un JWT vencido.
    """
    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "sub": "7",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
    )

    service = AccessTokenService(
        secret_key=TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
        expire_minutes=60,
    )

    with pytest.raises(
        InvalidAccessTokenError,
        match="invalido o ha vencido",
    ):
        service.get_user_id(token)
