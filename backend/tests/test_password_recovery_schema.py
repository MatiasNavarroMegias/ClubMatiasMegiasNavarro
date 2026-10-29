import pytest
from pydantic import ValidationError

from app.schemas import (
    PasswordRecoveryConfirm,
    PasswordRecoveryMessage,
    PasswordRecoveryRequest,
)


def test_password_recovery_request_normalizes_email():
    """
    Verifica que el correo se normalice antes de buscar al usuario.
    """
    recovery_request = PasswordRecoveryRequest(
        email="MATIAS@EXAMPLE.COM",
    )

    assert recovery_request.email == "matias@example.com"


@pytest.mark.parametrize(
    "email",
    [
        "correo-invalido",
        "matias@",
    ],
)
def test_password_recovery_request_rejects_invalid_email(
    email,
):
    """
    Verifica que la solicitud requiera un correo valido.
    """
    with pytest.raises(ValidationError):
        PasswordRecoveryRequest(
            email=email,
        )


def test_password_recovery_request_rejects_extra_fields():
    """
    Verifica que no puedan enviarse campos desconocidos.
    """
    with pytest.raises(ValidationError):
        PasswordRecoveryRequest.model_validate(
            {
                "email": "matias@example.com",
                "user_id": 999,
            }
        )


def test_password_recovery_confirm_accepts_valid_data():
    """
    Verifica una confirmacion de recuperacion valida.
    """
    confirmation = PasswordRecoveryConfirm(
        email="MATIAS@EXAMPLE.COM",
        code="48392175",
        new_password="NuevaClave123",
        new_password_confirmation="NuevaClave123",
    )

    assert confirmation.email == "matias@example.com"
    assert confirmation.code == "48392175"
    assert confirmation.new_password == "NuevaClave123"
    assert confirmation.new_password_confirmation == "NuevaClave123"


@pytest.mark.parametrize(
    "code",
    [
        "1234567",
        "123456789",
        "abcdefgh",
        "1234 678",
    ],
)
def test_password_recovery_confirm_rejects_invalid_code(
    code,
):
    """
    Verifica que el codigo contenga exactamente ocho digitos.
    """
    with pytest.raises(ValidationError):
        PasswordRecoveryConfirm(
            email="matias@example.com",
            code=code,
            new_password="NuevaClave123",
            new_password_confirmation="NuevaClave123",
        )


@pytest.mark.parametrize(
    "password",
    [
        "nuevaclave123",
        "NUEVACLAVE123",
        "NuevaClave",
        " NuevaClave123",
    ],
)
def test_password_recovery_confirm_rejects_insecure_password(
    password,
):
    """
    Verifica la politica de seguridad de la nueva contrasena.
    """
    with pytest.raises(ValidationError):
        PasswordRecoveryConfirm(
            email="matias@example.com",
            code="48392175",
            new_password=password,
            new_password_confirmation=password,
        )


def test_password_recovery_confirm_rejects_different_passwords():
    """
    Verifica que la confirmacion coincida con la nueva contrasena.
    """
    with pytest.raises(
        ValidationError,
        match="Las contrasenas ingresadas no coinciden",
    ):
        PasswordRecoveryConfirm(
            email="matias@example.com",
            code="48392175",
            new_password="NuevaClave123",
            new_password_confirmation="OtraClave456",
        )


def test_password_recovery_confirm_rejects_extra_fields():
    """
    Verifica que no puedan modificarse campos internos.
    """
    with pytest.raises(ValidationError):
        PasswordRecoveryConfirm.model_validate(
            {
                "email": "matias@example.com",
                "code": "48392175",
                "new_password": "NuevaClave123",
                "new_password_confirmation": "NuevaClave123",
                "failed_attempts": 0,
            }
        )


def test_password_recovery_message_contains_public_message():
    """
    Verifica la respuesta informativa del flujo.
    """
    response = PasswordRecoveryMessage(
        message=(
            "Si el correo pertenece a una cuenta, "
            "recibiras instrucciones para recuperar "
            "la contrasena."
        )
    )

    assert response.message == (
        "Si el correo pertenece a una cuenta, recibiras instrucciones para recuperar la contrasena."
    )
