from unittest.mock import patch

import pytest

from app.core.security import RecoveryCodeService


def test_recovery_code_service_generates_eight_digit_code():
    """
    Verifica que el codigo generado tenga ocho digitos.
    """
    service = RecoveryCodeService(
        secret_key="clave-secreta-de-prueba",
    )

    code = service.generate_code()

    assert len(code) == 8
    assert code.isdigit()


def test_recovery_code_service_preserves_leading_zeroes():
    """
    Verifica que el codigo conserve los ceros iniciales.
    """
    service = RecoveryCodeService(
        secret_key="clave-secreta-de-prueba",
    )

    with patch(
        "app.core.security.secrets.randbelow",
        return_value=123,
    ):
        code = service.generate_code()

    assert code == "00000123"


def test_recovery_code_service_uses_expected_random_limit():
    """
    Verifica el limite enviado al generador seguro.
    """
    service = RecoveryCodeService(
        secret_key="clave-secreta-de-prueba",
        code_length=8,
    )

    with patch(
        "app.core.security.secrets.randbelow",
        return_value=12345678,
    ) as mocked_randbelow:
        code = service.generate_code()

    assert code == "12345678"
    mocked_randbelow.assert_called_once_with(
        100000000,
    )


def test_recovery_code_service_supports_custom_length():
    """
    Verifica la generacion con una longitud personalizada.
    """
    service = RecoveryCodeService(
        secret_key="clave-secreta-de-prueba",
        code_length=6,
    )

    with patch(
        "app.core.security.secrets.randbelow",
        return_value=42,
    ):
        code = service.generate_code()

    assert code == "000042"
    assert len(code) == 6


def test_recovery_code_service_creates_deterministic_digest():
    """
    Verifica que el mismo codigo y clave produzcan el mismo resumen.
    """
    service = RecoveryCodeService(
        secret_key="clave-secreta-de-prueba",
    )

    first_digest = service.create_digest(
        "12345678",
    )
    second_digest = service.create_digest(
        "12345678",
    )

    assert first_digest == second_digest


def test_recovery_code_service_creates_sha256_digest():
    """
    Verifica que el resumen hexadecimal tenga 64 caracteres.
    """
    service = RecoveryCodeService(
        secret_key="clave-secreta-de-prueba",
    )

    digest = service.create_digest(
        "12345678",
    )

    assert len(digest) == 64

    integer_value = int(
        digest,
        16,
    )

    assert integer_value >= 0


def test_recovery_code_service_accepts_correct_code():
    """
    Verifica la comparacion de un codigo correcto.
    """
    service = RecoveryCodeService(
        secret_key="clave-secreta-de-prueba",
    )

    digest = service.create_digest(
        "12345678",
    )

    result = service.verify_code(
        "12345678",
        digest,
    )

    assert result is True


def test_recovery_code_service_rejects_incorrect_code():
    """
    Verifica la comparacion de un codigo incorrecto.
    """
    service = RecoveryCodeService(
        secret_key="clave-secreta-de-prueba",
    )

    digest = service.create_digest(
        "12345678",
    )

    result = service.verify_code(
        "87654321",
        digest,
    )

    assert result is False


def test_recovery_code_service_uses_constant_time_comparison():
    """
    Verifica el uso de una comparacion segura.
    """
    service = RecoveryCodeService(
        secret_key="clave-secreta-de-prueba",
    )

    stored_digest = service.create_digest(
        "12345678",
    )

    with patch(
        "app.core.security.hmac.compare_digest",
        return_value=True,
    ) as mocked_compare_digest:
        result = service.verify_code(
            "12345678",
            stored_digest,
        )

    assert result is True
    mocked_compare_digest.assert_called_once()

    received_digest = mocked_compare_digest.call_args.args[0]
    compared_stored_digest = mocked_compare_digest.call_args.args[1]

    assert received_digest == stored_digest
    assert compared_stored_digest == stored_digest


def test_recovery_code_service_different_keys_create_different_digests():
    """
    Verifica que claves diferentes produzcan resumenes diferentes.
    """
    first_service = RecoveryCodeService(
        secret_key="primera-clave-secreta",
    )
    second_service = RecoveryCodeService(
        secret_key="segunda-clave-secreta",
    )

    first_digest = first_service.create_digest(
        "12345678",
    )
    second_digest = second_service.create_digest(
        "12345678",
    )

    assert first_digest != second_digest


@pytest.mark.parametrize(
    "secret_key",
    [
        "",
        " ",
        "     ",
    ],
)
def test_recovery_code_service_rejects_empty_secret_key(
    secret_key,
):
    """
    Verifica que la clave privada no pueda estar vacia.
    """
    with pytest.raises(
        ValueError,
        match="clave de recuperacion no puede estar vacia",
    ):
        RecoveryCodeService(
            secret_key=secret_key,
        )


@pytest.mark.parametrize(
    "code_length",
    [
        0,
        1,
        5,
    ],
)
def test_recovery_code_service_rejects_short_codes(
    code_length,
):
    """
    Verifica que el codigo tenga al menos seis digitos.
    """
    with pytest.raises(
        ValueError,
        match="debe tener al menos seis digitos",
    ):
        RecoveryCodeService(
            secret_key="clave-secreta-de-prueba",
            code_length=code_length,
        )
