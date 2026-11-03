import pytest
from pydantic import ValidationError

from app.schemas import TokenResponse, UserLogin


def test_user_login_accepts_and_normalizes_valid_credentials() -> None:
    """
    Verifica que el login acepte credenciales validas.

    El correo se normaliza antes de consultar PostgreSQL, mientras que
    la contrasena conserva exactamente el valor recibido.
    """
    login_data = UserLogin(
        email="MATIAS@EXAMPLE.COM",
        password="ClaveSegura123",
    )

    assert login_data.email == "matias@example.com"
    assert login_data.password == "ClaveSegura123"


def test_user_login_rejects_invalid_email() -> None:
    """
    Verifica que el login rechace correos con formato invalido.
    """
    with pytest.raises(ValidationError):
        UserLogin(
            email="correo-invalido",
            password="ClaveSegura123",
        )


def test_user_login_rejects_empty_password() -> None:
    """
    Verifica que la contrasena no pueda estar vacia.
    """
    with pytest.raises(ValidationError):
        UserLogin(
            email="matias@example.com",
            password="",
        )


def test_user_login_rejects_password_longer_than_limit() -> None:
    """
    Verifica el limite maximo de 128 caracteres.
    """
    with pytest.raises(ValidationError):
        UserLogin(
            email="matias@example.com",
            password="A" * 129,
        )


def test_user_login_rejects_password_with_leading_space() -> None:
    """
    Verifica que la contrasena no comience con espacios.
    """
    with pytest.raises(
        ValidationError,
        match="no puede comenzar ni terminar con espacios",
    ):
        UserLogin(
            email="matias@example.com",
            password=" ClaveSegura123",
        )


def test_user_login_rejects_password_with_trailing_space() -> None:
    """
    Verifica que la contrasena no finalice con espacios.
    """
    with pytest.raises(
        ValidationError,
        match="no puede comenzar ni terminar con espacios",
    ):
        UserLogin(
            email="matias@example.com",
            password="ClaveSegura123 ",
        )


def test_user_login_preserves_internal_password_spaces() -> None:
    """
    Verifica que los espacios internos no se modifiquen.

    La contrasena debe compararse exactamente con el valor utilizado
    originalmente para producir el hash.
    """
    login_data = UserLogin(
        email="matias@example.com",
        password="Clave Segura 123",
    )

    assert login_data.password == "Clave Segura 123"


def test_user_login_does_not_require_registration_password_policy() -> None:
    """
    Verifica que el login no vuelva a aplicar la politica de registro.

    Una credencial debe verificarse contra su hash aunque una politica
    posterior sea mas estricta que la utilizada al crear la cuenta.
    """
    login_data = UserLogin(
        email="matias@example.com",
        password="password",
    )

    assert login_data.password == "password"


def test_token_response_uses_bearer_as_default_type() -> None:
    """
    Verifica el tipo predeterminado utilizado en Authorization.
    """
    response = TokenResponse(
        access_token="token-de-prueba",
    )

    assert response.access_token == "token-de-prueba"
    assert response.token_type == "bearer"


def test_token_response_does_not_expose_credentials() -> None:
    """
    Verifica que la respuesta contenga solamente datos del token.
    """
    response = TokenResponse(
        access_token="token-de-prueba",
    )
    response_data = response.model_dump()

    assert response_data == {
        "access_token": "token-de-prueba",
        "token_type": "bearer",
    }

    assert "password" not in response_data
    assert "password_hash" not in response_data
    assert "email" not in response_data
