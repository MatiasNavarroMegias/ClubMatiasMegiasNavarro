from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_password_recovery_service,
)
from app.core.security import (
    PasswordHasher,
    RecoveryCodeService,
)
from app.main import app
from app.repositories import (
    PasswordRecoveryRepository,
    UserRepository,
)
from app.services import (
    DevelopmentRecoveryCodeNotifier,
    InvalidPasswordRecoveryCodeError,
    PasswordRecoveryAttemptsExceededError,
    PasswordRecoveryService,
)

PUBLIC_MESSAGE = (
    "Si el correo pertenece a una cuenta, recibiras instrucciones para recuperar la contrasena."
)

SUCCESS_MESSAGE = "La contrasena fue actualizada correctamente."


def valid_request_json():
    """
    Construye una solicitud inicial valida.
    """
    return {
        "email": "matias@example.com",
    }


def valid_confirmation_json():
    """
    Construye una confirmacion valida.
    """
    return {
        "email": "matias@example.com",
        "code": "48392175",
        "new_password": "NuevaClave123",
        "new_password_confirmation": "NuevaClave123",
    }


@pytest.fixture
def password_recovery_api():
    """
    Construye un cliente HTTP con el servicio simulado.
    """
    service = MagicMock(
        spec=PasswordRecoveryService,
    )

    app.dependency_overrides[get_password_recovery_service] = lambda: service

    client = TestClient(app)

    return client, service


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """
    Limpia las dependencias simuladas despues de cada prueba.
    """
    yield
    app.dependency_overrides.clear()


def test_get_password_recovery_service_builds_dependencies():
    """
    Verifica la construccion real del servicio.
    """
    database_session = MagicMock(
        spec=Session,
    )

    service = get_password_recovery_service(
        database_session,
    )

    assert isinstance(
        service,
        PasswordRecoveryService,
    )
    assert isinstance(
        service.user_repository,
        UserRepository,
    )
    assert isinstance(
        service.recovery_repository,
        PasswordRecoveryRepository,
    )
    assert isinstance(
        service.code_service,
        RecoveryCodeService,
    )
    assert isinstance(
        service.password_hasher,
        PasswordHasher,
    )
    assert isinstance(
        service.notifier,
        DevelopmentRecoveryCodeNotifier,
    )

    assert service.user_repository.database_session is database_session
    assert service.recovery_repository.database_session is database_session
    assert service.expiration_minutes == 15
    assert service.maximum_attempts == 5


def test_get_password_recovery_service_rejects_console_notifier_in_production():
    """
    Verifica que la consola no pueda utilizarse en produccion.
    """
    database_session = MagicMock(
        spec=Session,
    )

    settings = MagicMock()
    settings.app_env = "production"
    settings.jwt_secret_key = "clave-secreta-de-produccion-con-longitud-segura"

    with patch(
        "app.api.dependencies.get_settings",
        return_value=settings,
    ):
        with pytest.raises(
            RuntimeError,
            match=("Debe configurar un notificador de recuperacion seguro"),
        ):
            get_password_recovery_service(
                database_session,
            )


def test_request_password_recovery_returns_generic_message(
    password_recovery_api,
):
    """
    Verifica la respuesta publica de la solicitud.
    """
    client, service = password_recovery_api

    service.request_recovery.return_value = PUBLIC_MESSAGE

    response = client.post(
        "/auth/password-recovery/request",
        json=valid_request_json(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": PUBLIC_MESSAGE,
    }

    service.request_recovery.assert_called_once()


def test_request_password_recovery_normalizes_email(
    password_recovery_api,
):
    """
    Verifica la normalizacion antes de llamar al servicio.
    """
    client, service = password_recovery_api

    service.request_recovery.return_value = PUBLIC_MESSAGE

    response = client.post(
        "/auth/password-recovery/request",
        json={
            "email": "MATIAS@EXAMPLE.COM",
        },
    )

    assert response.status_code == 200

    recovery_data = service.request_recovery.call_args.args[0]

    assert recovery_data.email == "matias@example.com"


def test_request_password_recovery_preserves_generic_unknown_email_response(
    password_recovery_api,
):
    """
    Verifica que la API no revele si el correo existe.
    """
    client, service = password_recovery_api

    service.request_recovery.return_value = PUBLIC_MESSAGE

    response = client.post(
        "/auth/password-recovery/request",
        json={
            "email": "desconocido@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": PUBLIC_MESSAGE,
    }


def test_request_password_recovery_rejects_invalid_email(
    password_recovery_api,
):
    """
    Verifica que un correo invalido produzca 422.
    """
    client, service = password_recovery_api

    response = client.post(
        "/auth/password-recovery/request",
        json={
            "email": "correo-invalido",
        },
    )

    assert response.status_code == 422
    service.request_recovery.assert_not_called()


def test_request_password_recovery_rejects_extra_fields(
    password_recovery_api,
):
    """
    Verifica que no puedan enviarse campos internos.
    """
    client, service = password_recovery_api

    response = client.post(
        "/auth/password-recovery/request",
        json={
            "email": "matias@example.com",
            "user_id": 7,
        },
    )

    assert response.status_code == 422
    service.request_recovery.assert_not_called()


def test_confirm_password_recovery_returns_success(
    password_recovery_api,
):
    """
    Verifica una confirmacion correcta.
    """
    client, service = password_recovery_api

    service.confirm_recovery.return_value = SUCCESS_MESSAGE

    response = client.post(
        "/auth/password-recovery/confirm",
        json=valid_confirmation_json(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": SUCCESS_MESSAGE,
    }

    service.confirm_recovery.assert_called_once()


def test_confirm_password_recovery_receives_normalized_data(
    password_recovery_api,
):
    """
    Verifica los datos entregados al servicio.
    """
    client, service = password_recovery_api

    service.confirm_recovery.return_value = SUCCESS_MESSAGE

    confirmation_json = valid_confirmation_json()
    confirmation_json["email"] = "MATIAS@EXAMPLE.COM"

    response = client.post(
        "/auth/password-recovery/confirm",
        json=confirmation_json,
    )

    assert response.status_code == 200

    confirmation_data = service.confirm_recovery.call_args.args[0]

    assert confirmation_data.email == ("matias@example.com")
    assert confirmation_data.code == "48392175"
    assert confirmation_data.new_password == ("NuevaClave123")


def test_confirm_password_recovery_returns_400_for_invalid_code(
    password_recovery_api,
):
    """
    Verifica el error de codigo invalido o vencido.
    """
    client, service = password_recovery_api

    service.confirm_recovery.side_effect = InvalidPasswordRecoveryCodeError(
        "El codigo de recuperacion no es valido o ha vencido."
    )

    response = client.post(
        "/auth/password-recovery/confirm",
        json=valid_confirmation_json(),
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": ("El codigo de recuperacion no es valido o ha vencido."),
    }


def test_confirm_password_recovery_returns_429_for_attempt_limit(
    password_recovery_api,
):
    """
    Verifica el limite de intentos del codigo.
    """
    client, service = password_recovery_api

    service.confirm_recovery.side_effect = PasswordRecoveryAttemptsExceededError(
        "El codigo de recuperacion supero la cantidad maxima de intentos."
    )

    response = client.post(
        "/auth/password-recovery/confirm",
        json=valid_confirmation_json(),
    )

    assert response.status_code == 429
    assert response.json() == {
        "detail": ("El codigo de recuperacion supero la cantidad maxima de intentos."),
    }


@pytest.mark.parametrize(
    "invalid_code",
    [
        "1234567",
        "123456789",
        "abcdefgh",
    ],
)
def test_confirm_password_recovery_rejects_invalid_code_format(
    password_recovery_api,
    invalid_code,
):
    """
    Verifica que el codigo tenga ocho digitos.
    """
    client, service = password_recovery_api

    confirmation_json = valid_confirmation_json()
    confirmation_json["code"] = invalid_code

    response = client.post(
        "/auth/password-recovery/confirm",
        json=confirmation_json,
    )

    assert response.status_code == 422
    service.confirm_recovery.assert_not_called()


def test_confirm_password_recovery_rejects_different_passwords(
    password_recovery_api,
):
    """
    Verifica que ambas contrasenas coincidan.
    """
    client, service = password_recovery_api

    confirmation_json = valid_confirmation_json()
    confirmation_json["new_password_confirmation"] = "OtraClave456"

    response = client.post(
        "/auth/password-recovery/confirm",
        json=confirmation_json,
    )

    assert response.status_code == 422
    service.confirm_recovery.assert_not_called()


def test_confirm_password_recovery_rejects_insecure_password(
    password_recovery_api,
):
    """
    Verifica la politica de seguridad de contrasenas.
    """
    client, service = password_recovery_api

    confirmation_json = valid_confirmation_json()
    confirmation_json["new_password"] = "nuevaclave123"
    confirmation_json["new_password_confirmation"] = "nuevaclave123"

    response = client.post(
        "/auth/password-recovery/confirm",
        json=confirmation_json,
    )

    assert response.status_code == 422
    service.confirm_recovery.assert_not_called()


def test_confirm_password_recovery_rejects_extra_fields(
    password_recovery_api,
):
    """
    Verifica que no puedan enviarse campos internos.
    """
    client, service = password_recovery_api

    confirmation_json = valid_confirmation_json()
    confirmation_json["failed_attempts"] = 0

    response = client.post(
        "/auth/password-recovery/confirm",
        json=confirmation_json,
    )

    assert response.status_code == 422
    service.confirm_recovery.assert_not_called()
