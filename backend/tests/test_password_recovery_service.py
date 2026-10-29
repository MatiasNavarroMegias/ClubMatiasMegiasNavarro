from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.core.security import PasswordHasher, RecoveryCodeService
from app.models import PasswordRecoveryToken, User
from app.repositories import (
    PasswordRecoveryRepository,
    UserRepository,
)
from app.schemas import (
    PasswordRecoveryConfirm,
    PasswordRecoveryRequest,
)
from app.services import (
    InvalidPasswordRecoveryCodeError,
    PasswordRecoveryAttemptsExceededError,
    PasswordRecoveryService,
)
from app.services.recovery_notifier import RecoveryCodeNotifier

CURRENT_DATETIME = datetime(
    2026,
    10,
    29,
    15,
    0,
    tzinfo=UTC,
)

PUBLIC_MESSAGE = (
    "Si el correo pertenece a una cuenta, recibiras instrucciones para recuperar la contrasena."
)

SUCCESS_MESSAGE = "La contrasena fue actualizada correctamente."


def create_user(
    user_id=7,
    email="matias@example.com",
    is_active=True,
):
    """
    Construye un usuario reutilizable para las pruebas.
    """
    audit_time = datetime(
        2026,
        10,
        20,
        12,
        0,
        tzinfo=UTC,
    )

    return User(
        id=user_id,
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(
            2000,
            1,
            15,
        ),
        email=email,
        password_hash="hash-anterior",
        is_active=is_active,
        created_at=audit_time,
        updated_at=audit_time,
    )


def create_recovery_token(
    token_id=1,
    user_id=7,
    code_digest="digest-generado",
    expires_at=None,
    used_at=None,
    failed_attempts=0,
):
    """
    Construye un codigo de recuperacion en memoria.
    """
    expiration = expires_at

    if expiration is None:
        expiration = CURRENT_DATETIME + timedelta(
            minutes=15,
        )

    return PasswordRecoveryToken(
        id=token_id,
        user_id=user_id,
        code_digest=code_digest,
        expires_at=expiration,
        used_at=used_at,
        failed_attempts=failed_attempts,
        created_at=CURRENT_DATETIME,
    )


def create_request():
    """
    Construye una solicitud valida.
    """
    return PasswordRecoveryRequest(
        email="matias@example.com",
    )


def create_confirmation(
    code="48392175",
    new_password="NuevaClave123",
):
    """
    Construye una confirmacion valida.
    """
    return PasswordRecoveryConfirm(
        email="matias@example.com",
        code=code,
        new_password=new_password,
        new_password_confirmation=new_password,
    )


def create_service(
    current_datetime=CURRENT_DATETIME,
    expiration_minutes=15,
    maximum_attempts=5,
):
    """
    Crea el servicio con todas sus dependencias simuladas.
    """
    user_repository = MagicMock(
        spec=UserRepository,
    )
    recovery_repository = MagicMock(
        spec=PasswordRecoveryRepository,
    )
    code_service = MagicMock(
        spec=RecoveryCodeService,
    )
    password_hasher = MagicMock(
        spec=PasswordHasher,
    )
    notifier = MagicMock(
        spec=RecoveryCodeNotifier,
    )

    service = PasswordRecoveryService(
        user_repository=user_repository,
        recovery_repository=recovery_repository,
        code_service=code_service,
        password_hasher=password_hasher,
        notifier=notifier,
        now_provider=lambda: current_datetime,
        expiration_minutes=expiration_minutes,
        maximum_attempts=maximum_attempts,
    )

    return (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    )


def test_request_recovery_returns_generic_message_for_unknown_email():
    """
    Verifica que un correo inexistente no pueda identificarse.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user_repository.get_by_email.return_value = None

    result = service.request_recovery(
        create_request(),
    )

    assert result == PUBLIC_MESSAGE

    user_repository.get_by_email.assert_called_once_with(
        "matias@example.com",
    )
    recovery_repository.invalidate_unused_by_user.assert_not_called()
    recovery_repository.add.assert_not_called()
    code_service.generate_code.assert_not_called()
    password_hasher.hash.assert_not_called()
    notifier.send_recovery_code.assert_not_called()


def test_request_recovery_returns_generic_message_for_inactive_user():
    """
    Verifica que una cuenta inactiva tampoco sea revelada.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user_repository.get_by_email.return_value = create_user(
        is_active=False,
    )

    result = service.request_recovery(
        create_request(),
    )

    assert result == PUBLIC_MESSAGE
    recovery_repository.invalidate_unused_by_user.assert_not_called()
    recovery_repository.add.assert_not_called()
    code_service.generate_code.assert_not_called()
    password_hasher.hash.assert_not_called()
    notifier.send_recovery_code.assert_not_called()


def test_request_recovery_invalidates_previous_codes():
    """
    Verifica que una solicitud nueva invalide las anteriores.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user_repository.get_by_email.return_value = create_user()
    code_service.generate_code.return_value = "48392175"
    code_service.create_digest.return_value = "digest-generado"

    result = service.request_recovery(
        create_request(),
    )

    assert result == PUBLIC_MESSAGE

    recovery_repository.invalidate_unused_by_user.assert_called_once_with(
        user_id=7,
        invalidated_at=CURRENT_DATETIME,
    )

    password_hasher.hash.assert_not_called()


def test_request_recovery_persists_protected_code():
    """
    Verifica el codigo protegido y su vencimiento.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user_repository.get_by_email.return_value = create_user()
    code_service.generate_code.return_value = "48392175"
    code_service.create_digest.return_value = "digest-generado"

    service.request_recovery(
        create_request(),
    )

    code_service.generate_code.assert_called_once_with()
    code_service.create_digest.assert_called_once_with(
        "48392175",
    )

    recovery_repository.add.assert_called_once()

    saved_token = recovery_repository.add.call_args.args[0]

    assert saved_token.user_id == 7
    assert saved_token.code_digest == "digest-generado"
    assert saved_token.expires_at == (CURRENT_DATETIME + timedelta(minutes=15))
    assert saved_token.used_at is None
    assert saved_token.failed_attempts == 0
    assert saved_token.code_digest != "48392175"

    password_hasher.hash.assert_not_called()


def test_request_recovery_sends_original_code():
    """
    Verifica la entrega del codigo original al notificador.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user_repository.get_by_email.return_value = create_user()
    code_service.generate_code.return_value = "48392175"
    code_service.create_digest.return_value = "digest-generado"

    service.request_recovery(
        create_request(),
    )

    notifier.send_recovery_code.assert_called_once_with(
        email="matias@example.com",
        code="48392175",
    )

    password_hasher.hash.assert_not_called()


def test_confirm_recovery_rejects_unknown_user():
    """
    Verifica una confirmacion para una cuenta inexistente.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user_repository.get_by_email.return_value = None

    with pytest.raises(
        InvalidPasswordRecoveryCodeError,
        match="no es valido o ha vencido",
    ):
        service.confirm_recovery(
            create_confirmation(),
        )

    recovery_repository.get_latest_unused_by_user.assert_not_called()
    code_service.verify_code.assert_not_called()
    password_hasher.hash.assert_not_called()
    notifier.send_recovery_code.assert_not_called()


def test_confirm_recovery_rejects_inactive_user():
    """
    Verifica una confirmacion para una cuenta inactiva.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user_repository.get_by_email.return_value = create_user(
        is_active=False,
    )

    with pytest.raises(
        InvalidPasswordRecoveryCodeError,
        match="no es valido o ha vencido",
    ):
        service.confirm_recovery(
            create_confirmation(),
        )

    recovery_repository.get_latest_unused_by_user.assert_not_called()
    code_service.verify_code.assert_not_called()
    password_hasher.hash.assert_not_called()


def test_confirm_recovery_rejects_missing_code():
    """
    Verifica una cuenta sin codigo disponible.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user_repository.get_by_email.return_value = create_user()
    recovery_repository.get_latest_unused_by_user.return_value = None

    with pytest.raises(
        InvalidPasswordRecoveryCodeError,
        match="no es valido o ha vencido",
    ):
        service.confirm_recovery(
            create_confirmation(),
        )

    recovery_repository.get_latest_unused_by_user.assert_called_once_with(
        user_id=7,
    )
    code_service.verify_code.assert_not_called()
    password_hasher.hash.assert_not_called()


def test_confirm_recovery_rejects_expired_code():
    """
    Verifica que un codigo vencido quede invalidado.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user = create_user()
    token = create_recovery_token(
        expires_at=CURRENT_DATETIME - timedelta(seconds=1),
    )

    user_repository.get_by_email.return_value = user
    recovery_repository.get_latest_unused_by_user.return_value = token

    with pytest.raises(
        InvalidPasswordRecoveryCodeError,
        match="no es valido o ha vencido",
    ):
        service.confirm_recovery(
            create_confirmation(),
        )

    assert token.used_at == CURRENT_DATETIME

    recovery_repository.save.assert_called_once_with(
        token,
    )
    code_service.verify_code.assert_not_called()
    password_hasher.hash.assert_not_called()


def test_confirm_recovery_increments_failed_attempts():
    """
    Verifica un codigo incorrecto antes del limite.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user = create_user()
    token = create_recovery_token(
        failed_attempts=2,
    )

    user_repository.get_by_email.return_value = user
    recovery_repository.get_latest_unused_by_user.return_value = token
    code_service.verify_code.return_value = False

    with pytest.raises(
        InvalidPasswordRecoveryCodeError,
        match="no es valido o ha vencido",
    ):
        service.confirm_recovery(
            create_confirmation(),
        )

    assert token.failed_attempts == 3
    assert token.used_at is None

    recovery_repository.save.assert_called_once_with(
        token,
    )
    password_hasher.hash.assert_not_called()
    user_repository.save.assert_not_called()


def test_confirm_recovery_blocks_code_on_last_failed_attempt():
    """
    Verifica el bloqueo al alcanzar cinco intentos.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user = create_user()
    token = create_recovery_token(
        failed_attempts=4,
    )

    user_repository.get_by_email.return_value = user
    recovery_repository.get_latest_unused_by_user.return_value = token
    code_service.verify_code.return_value = False

    with pytest.raises(
        PasswordRecoveryAttemptsExceededError,
        match="cantidad maxima de intentos",
    ):
        service.confirm_recovery(
            create_confirmation(),
        )

    assert token.failed_attempts == 5
    assert token.used_at == CURRENT_DATETIME

    recovery_repository.save.assert_called_once_with(
        token,
    )
    password_hasher.hash.assert_not_called()
    user_repository.save.assert_not_called()


def test_confirm_recovery_rejects_already_blocked_code():
    """
    Verifica un codigo que ya alcanzo el limite.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user = create_user()
    token = create_recovery_token(
        failed_attempts=5,
    )

    user_repository.get_by_email.return_value = user
    recovery_repository.get_latest_unused_by_user.return_value = token

    with pytest.raises(
        PasswordRecoveryAttemptsExceededError,
        match="cantidad maxima de intentos",
    ):
        service.confirm_recovery(
            create_confirmation(),
        )

    assert token.used_at == CURRENT_DATETIME

    recovery_repository.save.assert_called_once_with(
        token,
    )
    code_service.verify_code.assert_not_called()
    password_hasher.hash.assert_not_called()


def test_confirm_recovery_updates_password_and_uses_code():
    """
    Verifica una recuperacion correcta.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user = create_user()
    token = create_recovery_token()

    user_repository.get_by_email.return_value = user
    recovery_repository.get_latest_unused_by_user.return_value = token
    code_service.verify_code.return_value = True
    password_hasher.hash.return_value = "nuevo-hash-seguro"

    result = service.confirm_recovery(
        create_confirmation(),
    )

    assert result == SUCCESS_MESSAGE
    assert user.password_hash == "nuevo-hash-seguro"
    assert token.used_at == CURRENT_DATETIME

    code_service.verify_code.assert_called_once_with(
        "48392175",
        "digest-generado",
    )
    password_hasher.hash.assert_called_once_with(
        "NuevaClave123",
    )
    user_repository.save.assert_called_once_with(
        user,
    )
    recovery_repository.save.assert_called_once_with(
        token,
    )
    notifier.send_recovery_code.assert_not_called()


def test_service_rejects_naive_current_datetime():
    """
    Verifica que el reloj incluya zona horaria.
    """
    naive_datetime = datetime(
        2026,
        10,
        29,
        15,
        0,
    )

    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service(
        current_datetime=naive_datetime,
    )

    user_repository.get_by_email.return_value = create_user()

    with pytest.raises(
        ValueError,
        match="proveedor de fecha actual debe devolver",
    ):
        service.request_recovery(
            create_request(),
        )

    recovery_repository.invalidate_unused_by_user.assert_not_called()
    recovery_repository.add.assert_not_called()
    code_service.generate_code.assert_not_called()
    password_hasher.hash.assert_not_called()
    notifier.send_recovery_code.assert_not_called()


def test_service_rejects_naive_expiration_datetime():
    """
    Verifica que el vencimiento persistido tenga zona horaria.
    """
    (
        service,
        user_repository,
        recovery_repository,
        code_service,
        password_hasher,
        notifier,
    ) = create_service()

    user_repository.get_by_email.return_value = create_user()
    recovery_repository.get_latest_unused_by_user.return_value = create_recovery_token(
        expires_at=datetime(
            2026,
            10,
            29,
            15,
            15,
        ),
    )

    with pytest.raises(
        ValueError,
        match="fecha de vencimiento debe incluir",
    ):
        service.confirm_recovery(
            create_confirmation(),
        )

    code_service.verify_code.assert_not_called()
    password_hasher.hash.assert_not_called()
    user_repository.save.assert_not_called()
    notifier.send_recovery_code.assert_not_called()


@pytest.mark.parametrize(
    "expiration_minutes",
    [
        0,
        -1,
    ],
)
def test_service_rejects_invalid_expiration_minutes(
    expiration_minutes,
):
    """
    Verifica que la duracion configurada sea positiva.
    """
    with pytest.raises(
        ValueError,
        match="duracion del codigo debe ser mayor",
    ):
        create_service(
            expiration_minutes=expiration_minutes,
        )


@pytest.mark.parametrize(
    "maximum_attempts",
    [
        0,
        -1,
    ],
)
def test_service_rejects_invalid_maximum_attempts(
    maximum_attempts,
):
    """
    Verifica que la cantidad de intentos sea positiva.
    """
    with pytest.raises(
        ValueError,
        match="cantidad maxima de intentos debe ser",
    ):
        create_service(
            maximum_attempts=maximum_attempts,
        )
