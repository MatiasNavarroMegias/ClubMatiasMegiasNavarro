from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.security import (
    AccessTokenService,
    InvalidAccessTokenError,
)

TEST_SECRET_KEY = "test-secret-key-with-at-least-32-characters"
OTHER_SECRET_KEY = "other-secret-key-with-at-least-32-characters"
TEST_ALGORITHM = "HS256"
TEST_EXPIRE_MINUTES = 60


def create_token_service(
    *,
    secret_key: str = TEST_SECRET_KEY,
    expire_minutes: int = TEST_EXPIRE_MINUTES,
) -> AccessTokenService:
    """
    Construye un servicio reutilizable con configuracion ficticia.

    Las claves existen solamente durante las pruebas y no contienen
    secretos pertenecientes a ningun entorno real.
    """
    return AccessTokenService(
        secret_key=secret_key,
        algorithm=TEST_ALGORITHM,
        expire_minutes=expire_minutes,
    )


def test_create_access_token_contains_expected_claims() -> None:
    """
    Verifica que el token contenga identificador, emision y vencimiento.

    El token no debe incorporar datos innecesarios del perfil.
    """
    issued_at = datetime(2026, 10, 22, 15, 0, tzinfo=UTC)
    service = create_token_service()

    token = service.create_access_token(
        user_id=7,
        issued_at=issued_at,
    )

    payload = jwt.decode(
        token,
        TEST_SECRET_KEY,
        algorithms=[TEST_ALGORITHM],
        options={
            "verify_exp": False,
        },
    )

    assert payload["sub"] == "7"
    assert payload["iat"] == int(issued_at.timestamp())
    assert payload["exp"] == int((issued_at + timedelta(minutes=60)).timestamp())

    assert "password" not in payload
    assert "password_hash" not in payload
    assert "email" not in payload
    assert "birth_date" not in payload


def test_create_access_token_respects_configured_expiration() -> None:
    """
    Verifica que la duracion se obtenga desde la configuracion.

    Esta prueba utiliza una duracion diferente para demostrar que el
    valor no se encuentra fijo dentro del metodo.
    """
    issued_at = datetime(2026, 10, 22, 15, 0, tzinfo=UTC)
    service = create_token_service(
        expire_minutes=30,
    )

    token = service.create_access_token(
        user_id=15,
        issued_at=issued_at,
    )

    payload = jwt.decode(
        token,
        TEST_SECRET_KEY,
        algorithms=[TEST_ALGORITHM],
        options={
            "verify_exp": False,
        },
    )

    assert payload["exp"] - payload["iat"] == 30 * 60


def test_get_user_id_returns_subject_from_valid_token() -> None:
    """
    Verifica que un token valido permita recuperar el usuario.
    """
    service = create_token_service()

    token = service.create_access_token(user_id=25)

    user_id = service.get_user_id(token)

    assert user_id == 25


def test_get_user_id_rejects_expired_token() -> None:
    """
    Verifica que un token vencido no pueda autenticar al usuario.
    """
    service = create_token_service(
        expire_minutes=60,
    )
    expired_issued_at = datetime.now(UTC) - timedelta(hours=2)

    token = service.create_access_token(
        user_id=7,
        issued_at=expired_issued_at,
    )

    with pytest.raises(
        InvalidAccessTokenError,
        match="invalido o ha vencido",
    ):
        service.get_user_id(token)


def test_get_user_id_rejects_token_signed_with_another_key() -> None:
    """
    Verifica que una firma generada con otra clave sea rechazada.
    """
    first_service = create_token_service(
        secret_key=TEST_SECRET_KEY,
    )
    second_service = create_token_service(
        secret_key=OTHER_SECRET_KEY,
    )

    token = first_service.create_access_token(user_id=7)

    with pytest.raises(
        InvalidAccessTokenError,
        match="invalido o ha vencido",
    ):
        second_service.get_user_id(token)


def test_get_user_id_rejects_malformed_token() -> None:
    """
    Verifica que un valor sin estructura JWT sea rechazado.
    """
    service = create_token_service()

    with pytest.raises(
        InvalidAccessTokenError,
        match="invalido o ha vencido",
    ):
        service.get_user_id("not-a-valid-jwt")


def test_get_user_id_rejects_token_without_subject() -> None:
    """
    Verifica que el token incluya la identidad del usuario.
    """
    service = create_token_service()
    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "iat": now,
            "exp": now + timedelta(minutes=60),
        },
        TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
    )

    with pytest.raises(
        InvalidAccessTokenError,
        match="no contiene un usuario valido",
    ):
        service.get_user_id(token)


def test_get_user_id_rejects_non_numeric_subject() -> None:
    """
    Verifica que sub represente un identificador numerico.
    """
    service = create_token_service()
    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "sub": "invalid-user-id",
            "iat": now,
            "exp": now + timedelta(minutes=60),
        },
        TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
    )

    with pytest.raises(
        InvalidAccessTokenError,
        match="invalido o ha vencido",
    ):
        service.get_user_id(token)


def test_get_user_id_rejects_non_positive_subject() -> None:
    """
    Verifica que el identificador del usuario sea mayor que cero.
    """
    service = create_token_service()
    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "sub": "0",
            "iat": now,
            "exp": now + timedelta(minutes=60),
        },
        TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
    )

    with pytest.raises(
        InvalidAccessTokenError,
        match="no contiene un usuario valido",
    ):
        service.get_user_id(token)
