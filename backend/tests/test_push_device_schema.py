from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas import (
    PushDeviceRegister,
    PushDeviceResponse,
)


def test_push_device_register_accepts_valid_android_data() -> None:
    """
    Verifica que el esquema acepte una instalacion Android valida.
    """
    registration = PushDeviceRegister(
        installation_id="firebase-installation-id-for-testing",
        platform="android",
    )

    assert registration.installation_id == "firebase-installation-id-for-testing"
    assert registration.platform == "android"


def test_push_device_register_normalizes_received_data() -> None:
    """
    Verifica que los textos sean normalizados antes de utilizarlos.

    Los espacios externos se eliminan y la plataforma se convierte
    a minusculas.
    """
    registration = PushDeviceRegister(
        installation_id="  firebase-installation-id  ",
        platform="  ANDROID  ",
    )

    assert registration.installation_id == ("firebase-installation-id")
    assert registration.platform == "android"


def test_push_device_register_rejects_empty_installation_id() -> None:
    """
    Verifica que el identificador no pueda contener solo espacios.
    """
    with pytest.raises(
        ValidationError,
        match="no puede estar vacio",
    ):
        PushDeviceRegister(
            installation_id="   ",
            platform="android",
        )


def test_push_device_register_rejects_long_installation_id() -> None:
    """
    Verifica el limite definido por el modelo de datos.
    """
    with pytest.raises(ValidationError):
        PushDeviceRegister(
            installation_id="a" * 256,
            platform="android",
        )


def test_push_device_register_accepts_supported_platforms() -> None:
    """
    Verifica las plataformas contempladas por la aplicacion.
    """
    supported_platforms = (
        "android",
        "ios",
        "web",
    )

    for platform in supported_platforms:
        registration = PushDeviceRegister(
            installation_id=f"installation-id-{platform}",
            platform=platform,
        )

        assert registration.platform == platform


def test_push_device_register_rejects_unsupported_platform() -> None:
    """
    Verifica que no se almacenen plataformas desconocidas.
    """
    with pytest.raises(
        ValidationError,
        match="Plataforma no soportada",
    ):
        PushDeviceRegister(
            installation_id="firebase-installation-id",
            platform="windows",
        )


def test_push_device_register_rejects_extra_fields() -> None:
    """
    Verifica que el cliente no pueda enviar datos internos.

    El usuario debe obtenerse desde el JWT y el estado debe ser
    administrado exclusivamente por el backend.
    """
    protected_data = (
        {"user_id": 99},
        {"is_active": False},
        {"id": 15},
    )

    for extra_data in protected_data:
        with pytest.raises(ValidationError):
            PushDeviceRegister(
                installation_id="firebase-installation-id",
                platform="android",
                **extra_data,
            )


def test_push_device_response_accepts_model_attributes() -> None:
    """
    Verifica que la respuesta pueda construirse desde un modelo.

    El identificador de usuario puede devolverse porque representa
    al mismo usuario autenticado, pero nunca se recibe desde Flutter.
    """

    class PushDeviceData:
        id = 15
        user_id = 7
        installation_id = "firebase-installation-id"
        platform = "android"
        is_active = True
        created_at = datetime(
            2026,
            10,
            30,
            15,
            0,
            tzinfo=UTC,
        )
        updated_at = datetime(
            2026,
            10,
            30,
            15,
            0,
            tzinfo=UTC,
        )

    response = PushDeviceResponse.model_validate(
        PushDeviceData(),
    )

    assert response.id == 15
    assert response.user_id == 7
    assert response.installation_id == ("firebase-installation-id")
    assert response.platform == "android"
    assert response.is_active is True
    assert response.created_at == datetime(
        2026,
        10,
        30,
        15,
        0,
        tzinfo=UTC,
    )
