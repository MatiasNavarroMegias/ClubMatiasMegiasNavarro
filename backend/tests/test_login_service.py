from datetime import date
from unittest.mock import MagicMock

import pytest

from app.core.security import AccessTokenService, PasswordHasher
from app.models import User
from app.repositories import UserRepository
from app.schemas import UserLogin
from app.services import (
    AuthService,
    InactiveUserError,
    InvalidCredentialsError,
)


def create_user(
    *,
    is_active: bool = True,
) -> User:
    """
    Construye un usuario reutilizable para las pruebas del login.

    El usuario contiene un hash ficticio porque las operaciones
    criptograficas se reemplazan mediante PasswordHasher simulado.
    """
    return User(
        id=7,
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email="matias@example.com",
        password_hash="$argon2id$stored-hash",
        is_active=is_active,
    )


def create_login_data() -> UserLogin:
    """
    Construye credenciales validas y normalizadas.
    """
    return UserLogin(
        email="MATIAS@EXAMPLE.COM",
        password="ClaveSegura123",
    )


def create_auth_service() -> tuple[
    AuthService,
    MagicMock,
    MagicMock,
    MagicMock,
]:
    """
    Construye AuthService con dependencias simuladas.

    Esto permite probar solamente las reglas del inicio de sesion sin
    consultar PostgreSQL, ejecutar Argon2 ni firmar un JWT real.
    """
    repository = MagicMock(spec=UserRepository)
    password_hasher = MagicMock(spec=PasswordHasher)
    access_token_service = MagicMock(spec=AccessTokenService)

    service = AuthService(
        repository=repository,
        password_hasher=password_hasher,
        access_token_service=access_token_service,
    )

    return (
        service,
        repository,
        password_hasher,
        access_token_service,
    )


def test_login_user_returns_access_token_for_valid_credentials() -> None:
    """
    Verifica el flujo exitoso del inicio de sesion.
    """
    (
        service,
        repository,
        password_hasher,
        access_token_service,
    ) = create_auth_service()

    repository.get_by_email.return_value = create_user()
    password_hasher.verify.return_value = True
    access_token_service.create_access_token.return_value = "signed-access-token"

    token = service.login_user(create_login_data())

    assert token == "signed-access-token"

    repository.get_by_email.assert_called_once_with("matias@example.com")
    password_hasher.verify.assert_called_once_with(
        "ClaveSegura123",
        "$argon2id$stored-hash",
    )
    access_token_service.create_access_token.assert_called_once_with(
        user_id=7,
    )


def test_login_user_rejects_unknown_email() -> None:
    """
    Verifica que un correo inexistente produzca credenciales invalidas.
    """
    (
        service,
        repository,
        password_hasher,
        access_token_service,
    ) = create_auth_service()

    repository.get_by_email.return_value = None

    with pytest.raises(
        InvalidCredentialsError,
        match="Correo o contrasena incorrectos",
    ):
        service.login_user(create_login_data())

    repository.get_by_email.assert_called_once_with("matias@example.com")
    password_hasher.verify.assert_not_called()
    access_token_service.create_access_token.assert_not_called()


def test_login_user_rejects_incorrect_password() -> None:
    """
    Verifica que una contrasena incorrecta produzca el mismo error.

    El mensaje coincide con el utilizado para un correo desconocido
    para no revelar si una cuenta se encuentra registrada.
    """
    (
        service,
        repository,
        password_hasher,
        access_token_service,
    ) = create_auth_service()

    repository.get_by_email.return_value = create_user()
    password_hasher.verify.return_value = False

    with pytest.raises(
        InvalidCredentialsError,
        match="Correo o contrasena incorrectos",
    ):
        service.login_user(create_login_data())

    password_hasher.verify.assert_called_once_with(
        "ClaveSegura123",
        "$argon2id$stored-hash",
    )
    access_token_service.create_access_token.assert_not_called()


def test_unknown_email_and_incorrect_password_use_same_message() -> None:
    """
    Verifica que el servicio no revele si un correo esta registrado.
    """
    (
        unknown_email_service,
        unknown_email_repository,
        _,
        _,
    ) = create_auth_service()
    unknown_email_repository.get_by_email.return_value = None

    with pytest.raises(InvalidCredentialsError) as unknown_email_error:
        unknown_email_service.login_user(create_login_data())

    (
        wrong_password_service,
        wrong_password_repository,
        wrong_password_hasher,
        _,
    ) = create_auth_service()
    wrong_password_repository.get_by_email.return_value = create_user()
    wrong_password_hasher.verify.return_value = False

    with pytest.raises(InvalidCredentialsError) as wrong_password_error:
        wrong_password_service.login_user(create_login_data())

    assert str(unknown_email_error.value) == str(wrong_password_error.value)


def test_login_user_rejects_inactive_account() -> None:
    """
    Verifica que una cuenta inactiva no pueda obtener un token.
    """
    (
        service,
        repository,
        password_hasher,
        access_token_service,
    ) = create_auth_service()

    repository.get_by_email.return_value = create_user(
        is_active=False,
    )
    password_hasher.verify.return_value = True

    with pytest.raises(
        InactiveUserError,
        match="cuenta de usuario se encuentra inactiva",
    ):
        service.login_user(create_login_data())

    password_hasher.verify.assert_called_once()
    access_token_service.create_access_token.assert_not_called()


def test_login_user_requires_access_token_service() -> None:
    """
    Verifica que el login no funcione sin el servicio JWT configurado.
    """
    repository = MagicMock(spec=UserRepository)
    password_hasher = MagicMock(spec=PasswordHasher)

    repository.get_by_email.return_value = create_user()
    password_hasher.verify.return_value = True

    service = AuthService(
        repository=repository,
        password_hasher=password_hasher,
    )

    with pytest.raises(
        RuntimeError,
        match="servicio de tokens no se encuentra configurado",
    ):
        service.login_user(create_login_data())


def test_login_user_does_not_create_token_after_invalid_credentials() -> None:
    """
    Verifica que un error de credenciales detenga completamente el flujo.
    """
    (
        service,
        repository,
        password_hasher,
        access_token_service,
    ) = create_auth_service()

    repository.get_by_email.return_value = create_user()
    password_hasher.verify.return_value = False

    with pytest.raises(InvalidCredentialsError):
        service.login_user(create_login_data())

    access_token_service.create_access_token.assert_not_called()


def test_login_user_does_not_create_token_for_inactive_account() -> None:
    """
    Verifica que una cuenta inactiva nunca reciba un JWT.
    """
    (
        service,
        repository,
        password_hasher,
        access_token_service,
    ) = create_auth_service()

    repository.get_by_email.return_value = create_user(
        is_active=False,
    )
    password_hasher.verify.return_value = True

    with pytest.raises(InactiveUserError):
        service.login_user(create_login_data())

    access_token_service.create_access_token.assert_not_called()
