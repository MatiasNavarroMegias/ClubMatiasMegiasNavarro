from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models import User
from app.schemas import UserRegister, UserResponse


def valid_registration_data() -> dict:
    """
    Devuelve datos validos reutilizables para las pruebas.

    Cada prueba modifica solamente el campo relacionado con la regla
    que necesita verificar.
    """
    return {
        "first_name": "Matias",
        "last_name": "Megias Navarro",
        "birth_date": date(2000, 1, 15),
        "email": "matias@example.com",
        "password": "ClaveSegura123",
    }


def test_user_register_accepts_and_normalizes_valid_data() -> None:
    """
    Verifica que el registro acepte datos validos y normalice textos.
    """
    registration_data = valid_registration_data()
    registration_data.update(
        {
            "first_name": " Matias ",
            "last_name": " Megias Navarro ",
            "email": "MATIAS@EXAMPLE.COM",
        }
    )

    user_data = UserRegister(**registration_data)

    assert user_data.first_name == "Matias"
    assert user_data.last_name == "Megias Navarro"
    assert user_data.birth_date == date(2000, 1, 15)
    assert user_data.email == "matias@example.com"
    assert user_data.password == "ClaveSegura123"


def test_user_register_rejects_invalid_email() -> None:
    """
    Verifica que el correo posea una estructura valida.
    """
    registration_data = valid_registration_data()
    registration_data["email"] = "correo-invalido"

    with pytest.raises(ValidationError):
        UserRegister(**registration_data)


def test_user_register_rejects_first_name_with_only_spaces() -> None:
    """
    Verifica que el nombre no pueda contener solamente espacios.
    """
    registration_data = valid_registration_data()
    registration_data["first_name"] = "   "

    with pytest.raises(
        ValidationError,
        match="no pueden contener solo espacios",
    ):
        UserRegister(**registration_data)


def test_user_register_rejects_last_name_with_only_spaces() -> None:
    """
    Verifica que el apellido no pueda contener solamente espacios.
    """
    registration_data = valid_registration_data()
    registration_data["last_name"] = "   "

    with pytest.raises(
        ValidationError,
        match="no pueden contener solo espacios",
    ):
        UserRegister(**registration_data)


def test_user_register_rejects_current_birth_date() -> None:
    """
    Verifica que la fecha de nacimiento no pueda ser el dia actual.
    """
    registration_data = valid_registration_data()
    registration_data["birth_date"] = date.today()

    with pytest.raises(
        ValidationError,
        match="debe ser anterior al dia actual",
    ):
        UserRegister(**registration_data)


def test_user_register_rejects_future_birth_date() -> None:
    """
    Verifica que la fecha de nacimiento no pueda estar en el futuro.
    """
    registration_data = valid_registration_data()
    registration_data["birth_date"] = date.today() + timedelta(days=1)

    with pytest.raises(
        ValidationError,
        match="debe ser anterior al dia actual",
    ):
        UserRegister(**registration_data)


def test_user_register_rejects_short_password() -> None:
    """
    Verifica la longitud minima de ocho caracteres.
    """
    registration_data = valid_registration_data()
    registration_data["password"] = "Clave1"

    with pytest.raises(ValidationError):
        UserRegister(**registration_data)


def test_user_register_rejects_password_without_uppercase_letter() -> None:
    """
    Verifica que la contrasena contenga una letra mayuscula.
    """
    registration_data = valid_registration_data()
    registration_data["password"] = "clavesegura123"

    with pytest.raises(
        ValidationError,
        match="al menos una letra mayuscula",
    ):
        UserRegister(**registration_data)


def test_user_register_rejects_password_without_lowercase_letter() -> None:
    """
    Verifica que la contrasena contenga una letra minuscula.
    """
    registration_data = valid_registration_data()
    registration_data["password"] = "CLAVESEGURA123"

    with pytest.raises(
        ValidationError,
        match="al menos una letra minuscula",
    ):
        UserRegister(**registration_data)


def test_user_register_rejects_password_without_number() -> None:
    """
    Verifica que la contrasena contenga al menos un numero.
    """
    registration_data = valid_registration_data()
    registration_data["password"] = "ClaveSegura"

    with pytest.raises(
        ValidationError,
        match="al menos un numero",
    ):
        UserRegister(**registration_data)


def test_user_register_rejects_password_with_external_spaces() -> None:
    """
    Verifica que la contrasena no comience ni finalice con espacios.

    La contrasena no se normaliza automaticamente porque eliminar
    caracteres podria cambiar silenciosamente el valor elegido.
    """
    registration_data = valid_registration_data()
    registration_data["password"] = " ClaveSegura123 "

    with pytest.raises(
        ValidationError,
        match="no puede comenzar ni terminar con espacios",
    ):
        UserRegister(**registration_data)


def test_user_register_rejects_first_name_longer_than_limit() -> None:
    """
    Verifica el limite de 50 caracteres definido para el nombre.
    """
    registration_data = valid_registration_data()
    registration_data["first_name"] = "A" * 51

    with pytest.raises(ValidationError):
        UserRegister(**registration_data)


def test_user_register_rejects_password_longer_than_limit() -> None:
    """
    Verifica el limite maximo de 128 caracteres de la contrasena.
    """
    registration_data = valid_registration_data()
    registration_data["password"] = f"Aa1{'x' * 126}"

    with pytest.raises(ValidationError):
        UserRegister(**registration_data)


def test_user_response_can_be_created_without_exposing_credentials() -> None:
    """
    Verifica la conversion desde SQLAlchemy y la respuesta publica.

    La respuesta debe excluir tanto la contrasena original como el hash.
    """
    audit_time = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)

    user = User(
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

    response = UserResponse.model_validate(user)
    response_data = response.model_dump()

    assert response.id == 1
    assert response.first_name == "Matias"
    assert response.last_name == "Megias Navarro"
    assert response.birth_date == date(2000, 1, 15)
    assert response.email == "matias@example.com"
    assert response.is_active is True
    assert response.created_at == audit_time
    assert response.updated_at == audit_time

    assert "password" not in response_data
    assert "password_hash" not in response_data
