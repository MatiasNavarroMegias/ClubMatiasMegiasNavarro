from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.core.security import PasswordHasher, RecoveryCodeService
from app.models import PasswordRecoveryToken
from app.repositories import (
    PasswordRecoveryRepository,
    UserRepository,
)
from app.schemas import (
    PasswordRecoveryConfirm,
    PasswordRecoveryRequest,
)
from app.services.recovery_notifier import RecoveryCodeNotifier


class InvalidPasswordRecoveryCodeError(Exception):
    """
    Indica que el codigo no existe, vencio o no es valido.

    Se utiliza un unico error para no revelar detalles sobre la cuenta
    ni sobre el estado exacto del codigo temporal.
    """


class PasswordRecoveryAttemptsExceededError(Exception):
    """
    Indica que el codigo supero la cantidad maxima de intentos.
    """


class PasswordRecoveryService:
    """
    Aplica las reglas de recuperacion segura de contrasena.

    El servicio genera codigos temporales, protege su almacenamiento,
    controla su vencimiento y limita los intentos de verificacion.
    """

    public_request_message = (
        "Si el correo pertenece a una cuenta, recibiras instrucciones para recuperar la contrasena."
    )

    success_message = "La contrasena fue actualizada correctamente."

    def __init__(
        self,
        user_repository: UserRepository,
        recovery_repository: PasswordRecoveryRepository,
        code_service: RecoveryCodeService,
        password_hasher: PasswordHasher,
        notifier: RecoveryCodeNotifier,
        now_provider: Callable = None,
        expiration_minutes: int = 15,
        maximum_attempts: int = 5,
    ) -> None:
        """
        Inicializa el servicio con dependencias reemplazables.

        Args:
            user_repository: Repositorio de usuarios.
            recovery_repository: Repositorio de codigos temporales.
            code_service: Generador y verificador HMAC.
            password_hasher: Servicio Argon2 para contrasenas.
            notifier: Mecanismo utilizado para entregar el codigo.
            now_provider: Reloj opcional para pruebas automatizadas.
            expiration_minutes: Duracion del codigo.
            maximum_attempts: Intentos incorrectos permitidos.

        Raises:
            ValueError: Cuando la configuracion no es valida.
        """
        if expiration_minutes <= 0:
            raise ValueError("La duracion del codigo debe ser mayor que cero.")

        if maximum_attempts <= 0:
            raise ValueError("La cantidad maxima de intentos debe ser mayor que cero.")

        self.user_repository = user_repository
        self.recovery_repository = recovery_repository
        self.code_service = code_service
        self.password_hasher = password_hasher
        self.notifier = notifier
        self.now_provider = now_provider if now_provider is not None else self._current_datetime
        self.expiration_minutes = expiration_minutes
        self.maximum_attempts = maximum_attempts

    def request_recovery(
        self,
        recovery_data: PasswordRecoveryRequest,
    ) -> str:
        """
        Genera un codigo para una cuenta existente y activa.

        La respuesta publica es siempre la misma, aunque el correo no
        pertenezca a una cuenta. Esto evita revelar usuarios registrados.

        Args:
            recovery_data: Correo validado y normalizado.

        Returns:
            Mensaje publico generico.
        """
        user = self.user_repository.get_by_email(
            recovery_data.email,
        )

        if user is None or not user.is_active:
            return self.public_request_message

        current_datetime = self._get_current_datetime()

        self.recovery_repository.invalidate_unused_by_user(
            user_id=user.id,
            invalidated_at=current_datetime,
        )

        generated_code = self.code_service.generate_code()

        recovery_token = PasswordRecoveryToken(
            user_id=user.id,
            code_digest=self.code_service.create_digest(
                generated_code,
            ),
            expires_at=current_datetime
            + timedelta(
                minutes=self.expiration_minutes,
            ),
            used_at=None,
            failed_attempts=0,
        )

        self.recovery_repository.add(
            recovery_token,
        )

        self.notifier.send_recovery_code(
            email=user.email,
            code=generated_code,
        )

        return self.public_request_message

    def confirm_recovery(
        self,
        confirmation_data: PasswordRecoveryConfirm,
    ) -> str:
        """
        Verifica un codigo y reemplaza la contrasena.

        Args:
            confirmation_data: Correo, codigo y nueva contrasena.

        Returns:
            Mensaje de recuperacion correcta.

        Raises:
            InvalidPasswordRecoveryCodeError: Cuando la cuenta o el
                codigo no pueden utilizarse.
            PasswordRecoveryAttemptsExceededError: Cuando se alcanzo
                el limite de intentos.
        """
        user = self.user_repository.get_by_email(
            confirmation_data.email,
        )

        if user is None or not user.is_active:
            raise InvalidPasswordRecoveryCodeError(
                "El codigo de recuperacion no es valido o ha vencido."
            )

        recovery_token = self.recovery_repository.get_latest_unused_by_user(
            user_id=user.id,
        )

        if recovery_token is None:
            raise InvalidPasswordRecoveryCodeError(
                "El codigo de recuperacion no es valido o ha vencido."
            )

        current_datetime = self._get_current_datetime()

        if recovery_token.failed_attempts >= self.maximum_attempts:
            recovery_token.used_at = current_datetime

            self.recovery_repository.save(
                recovery_token,
            )

            raise PasswordRecoveryAttemptsExceededError(
                "El codigo de recuperacion supero la cantidad maxima de intentos."
            )

        expires_at = self._normalize_datetime(
            recovery_token.expires_at,
        )

        if expires_at <= current_datetime:
            recovery_token.used_at = current_datetime

            self.recovery_repository.save(
                recovery_token,
            )

            raise InvalidPasswordRecoveryCodeError(
                "El codigo de recuperacion no es valido o ha vencido."
            )

        code_matches = self.code_service.verify_code(
            confirmation_data.code,
            recovery_token.code_digest,
        )

        if not code_matches:
            recovery_token.failed_attempts += 1

            if recovery_token.failed_attempts >= self.maximum_attempts:
                recovery_token.used_at = current_datetime

            self.recovery_repository.save(
                recovery_token,
            )

            if recovery_token.failed_attempts >= self.maximum_attempts:
                raise PasswordRecoveryAttemptsExceededError(
                    "El codigo de recuperacion supero la cantidad maxima de intentos."
                )

            raise InvalidPasswordRecoveryCodeError(
                "El codigo de recuperacion no es valido o ha vencido."
            )

        user.password_hash = self.password_hasher.hash(
            confirmation_data.new_password,
        )

        self.user_repository.save(
            user,
        )

        recovery_token.used_at = current_datetime

        self.recovery_repository.save(
            recovery_token,
        )

        return self.success_message

    def _current_datetime(self) -> datetime:
        """
        Devuelve el momento actual en UTC.
        """
        return datetime.now(
            UTC,
        )

    def _get_current_datetime(self) -> datetime:
        """
        Obtiene el momento actual y lo convierte a UTC.

        Raises:
            ValueError: Cuando el reloj devuelve una fecha sin zona.
        """
        current_datetime = self.now_provider()

        if current_datetime.tzinfo is None or current_datetime.utcoffset() is None:
            raise ValueError(
                "El proveedor de fecha actual debe devolver una fecha con zona horaria."
            )

        return current_datetime.astimezone(
            UTC,
        )

    def _normalize_datetime(
        self,
        value: datetime,
    ) -> datetime:
        """
        Convierte una fecha persistida a UTC.

        Raises:
            ValueError: Cuando la fecha no tiene zona horaria.
        """
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("La fecha de vencimiento debe incluir una zona horaria.")

        return value.astimezone(
            UTC,
        )
