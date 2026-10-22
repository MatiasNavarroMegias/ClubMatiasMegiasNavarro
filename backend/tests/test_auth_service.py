from datetime import date
from unittest.mock import MagicMock

import pytest
from pwdlib import PasswordHash

from app.core.security import PasswordHasher
from app.models import User
from app.repositories import UserRepository
from app.schemas import UserRegister
from app.services import (
    AuthService,
    EmailAlreadyRegisteredError,
)


def create_registration_data() -> UserRegister:
    """
    Construye datos validos para registrar un usuario.

    La contrasena existe solamente dentro del esquema de entrada y
    posteriormente debe transformarse en un hash seguro.
    """
    return UserRegister(
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email="matias@example.com",
        password="ClaveSegura123",
    )


def test_password_hasher_generates_argon2_hash_and_verifies_password() -> None:
    """
    Verifica el hashing real mediante la configuracion recomendada.

    La contrasena original no debe coincidir directamente con el
    valor almacenado.
    """
    password_hasher = PasswordHasher()

    password_hash = password_hasher.hash("ClaveSegura123")

    assert password_hash != "ClaveSegura123"
    assert password_hash.startswith("$argon2")
    assert password_hasher.verify(
        "ClaveSegura123",
        password_hash,
    )
    assert not password_hasher.verify(
        "ClaveIncorrecta",
        password_hash,
    )


def test_password_hasher_delegates_to_injected_implementation() -> None:
    """
    Verifica que PasswordHasher permita reemplazar pwdlib en las pruebas.

    Esta inyeccion evita ejecutar operaciones criptograficas reales
    cuando se prueban solamente las reglas de negocio.
    """
    password_hash_implementation = MagicMock(spec=PasswordHash)
    password_hash_implementation.hash.return_value = "generated-hash"
    password_hash_implementation.verify.return_value = True

    password_hasher = PasswordHasher(password_hash_implementation)

    generated_hash = password_hasher.hash("ClaveSegura123")
    password_matches = password_hasher.verify(
        "ClaveSegura123",
        "stored-hash",
    )

    assert generated_hash == "generated-hash"
    assert password_matches is True

    password_hash_implementation.hash.assert_called_once_with("ClaveSegura123")
    password_hash_implementation.verify.assert_called_once_with(
        "ClaveSegura123",
        "stored-hash",
    )


def test_register_user_hashes_password_and_persists_user() -> None:
    """
    Verifica el flujo completo de registracion en la capa de servicio.

    El servicio consulta el correo, genera el hash y entrega el modelo
    al repositorio.
    """
    repository = MagicMock(spec=UserRepository)
    password_hasher = MagicMock(spec=PasswordHasher)

    repository.get_by_email.return_value = None
    repository.add.side_effect = lambda user: user
    password_hasher.hash.return_value = "$argon2id$generated-hash"

    service = AuthService(
        repository=repository,
        password_hasher=password_hasher,
    )
    registration_data = create_registration_data()

    user = service.register_user(registration_data)

    assert user.first_name == "Matias"
    assert user.last_name == "Megias Navarro"
    assert user.birth_date == date(2000, 1, 15)
    assert user.email == "matias@example.com"
    assert user.password_hash == "$argon2id$generated-hash"
    assert user.is_active is True

    repository.get_by_email.assert_called_once_with("matias@example.com")
    password_hasher.hash.assert_called_once_with("ClaveSegura123")
    repository.add.assert_called_once_with(user)


def test_register_user_never_persists_plain_password() -> None:
    """
    Verifica que el modelo persistido no contenga la contrasena original.

    La contrasena pertenece solamente al esquema de registracion.
    """
    repository = MagicMock(spec=UserRepository)
    password_hasher = MagicMock(spec=PasswordHasher)

    repository.get_by_email.return_value = None
    repository.add.side_effect = lambda user: user
    password_hasher.hash.return_value = "$argon2id$generated-hash"

    service = AuthService(
        repository=repository,
        password_hasher=password_hasher,
    )

    service.register_user(create_registration_data())

    persisted_user = repository.add.call_args.args[0]

    assert isinstance(persisted_user, User)
    assert persisted_user.password_hash == "$argon2id$generated-hash"
    assert not hasattr(persisted_user, "password")
    assert not hasattr(persisted_user, "plain_password")


def test_register_user_rejects_already_registered_email() -> None:
    """
    Verifica que un correo existente produzca un error de negocio.
    """
    repository = MagicMock(spec=UserRepository)
    password_hasher = MagicMock(spec=PasswordHasher)

    repository.get_by_email.return_value = User(
        first_name="Existing",
        last_name="User",
        birth_date=date(1995, 5, 20),
        email="matias@example.com",
        password_hash="$argon2id$existing-hash",
        is_active=True,
    )

    service = AuthService(
        repository=repository,
        password_hasher=password_hasher,
    )

    with pytest.raises(
        EmailAlreadyRegisteredError,
        match="Ya existe un usuario registrado con ese correo",
    ):
        service.register_user(create_registration_data())

    repository.get_by_email.assert_called_once_with("matias@example.com")


def test_duplicate_email_does_not_hash_or_persist_password() -> None:
    """
    Verifica que el servicio se detenga antes de ejecutar operaciones costosas.

    Si el correo ya existe, no es necesario generar un hash Argon2 ni
    intentar guardar otro usuario.
    """
    repository = MagicMock(spec=UserRepository)
    password_hasher = MagicMock(spec=PasswordHasher)

    repository.get_by_email.return_value = User(
        first_name="Existing",
        last_name="User",
        birth_date=date(1995, 5, 20),
        email="matias@example.com",
        password_hash="$argon2id$existing-hash",
        is_active=True,
    )

    service = AuthService(
        repository=repository,
        password_hasher=password_hasher,
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register_user(create_registration_data())

    password_hasher.hash.assert_not_called()
    repository.add.assert_not_called()
