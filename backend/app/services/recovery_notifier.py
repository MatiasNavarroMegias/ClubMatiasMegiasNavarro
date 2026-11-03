import json
import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class RecoveryCodeDeliveryError(Exception):
    """Indica que un proveedor externo no pudo entregar el codigo."""


class RecoveryCodeNotifier(Protocol):
    """
    Define el mecanismo utilizado para entregar un codigo.

    El servicio de recuperacion depende de esta abstraccion y no de
    una tecnologia especifica como SMTP o un proveedor externo.
    """

    def send_recovery_code(
        self,
        email: str,
        code: str,
    ) -> None:
        """
        Entrega un codigo de recuperacion al correo indicado.

        Args:
            email: Correo normalizado del usuario.
            code: Codigo temporal generado para la recuperacion.
        """


class DevelopmentRecoveryCodeNotifier:
    """
    Muestra el codigo de recuperacion en la consola de desarrollo.

    Esta implementacion facilita probar el flujo completo localmente
    sin configurar credenciales de correo. No debe utilizarse en el
    entorno de produccion.
    """

    def send_recovery_code(
        self,
        email: str,
        code: str,
    ) -> None:
        """
        Muestra el codigo temporal en la consola.

        Args:
            email: Correo normalizado del usuario.
            code: Codigo temporal generado.
        """
        logger.info(
            "Codigo de recuperacion generado para entorno no productivo.",
            extra={"email": email, "code": code},
        )


class SMTPRecoveryCodeNotifier:
    """Entrega codigos mediante un servidor SMTP configurado por entorno."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        sender: str,
        use_tls: bool,
        timeout_seconds: int = 10,
    ) -> None:
        if not host.strip():
            raise ValueError("El servidor SMTP no puede estar vacio.")
        if port <= 0 or port > 65535:
            raise ValueError("El puerto SMTP no es valido.")
        if not sender.strip():
            raise ValueError("El remitente SMTP no puede estar vacio.")
        if timeout_seconds <= 0:
            raise ValueError("El tiempo de espera SMTP debe ser mayor que cero.")

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender
        self.use_tls = use_tls
        self.timeout_seconds = timeout_seconds

    def send_recovery_code(
        self,
        email: str,
        code: str,
    ) -> None:
        message = EmailMessage()
        message["Subject"] = "Recuperacion de contrasena"
        message["From"] = self.sender
        message["To"] = email
        message.set_content(
            "Solicitaste recuperar tu contrasena.\n\n"
            f"Tu codigo temporal es: {code}\n"
            "Este codigo vence en 15 minutos y solo puede utilizarse una vez."
        )

        with smtplib.SMTP(
            self.host,
            self.port,
            timeout=self.timeout_seconds,
        ) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.username:
                smtp.login(self.username, self.password or "")
            smtp.send_message(message)


class BrevoRecoveryCodeNotifier:
    """Entrega codigos mediante la API HTTPS transaccional de Brevo."""

    def __init__(
        self,
        *,
        api_key: str,
        sender: str,
        sender_name: str,
        api_url: str,
        timeout_seconds: int = 10,
    ) -> None:
        if not api_key.strip():
            raise ValueError("La API key de Brevo no puede estar vacia.")
        if not sender.strip():
            raise ValueError("El remitente de Brevo no puede estar vacio.")
        if not sender_name.strip():
            raise ValueError("El nombre del remitente de Brevo no puede estar vacio.")
        if not api_url.strip():
            raise ValueError("La URL de Brevo no puede estar vacia.")
        if timeout_seconds <= 0:
            raise ValueError("El tiempo de espera de Brevo debe ser mayor que cero.")

        self.api_key = api_key
        self.sender = sender
        self.sender_name = sender_name
        self.api_url = api_url
        self.timeout_seconds = timeout_seconds

    def send_recovery_code(self, email: str, code: str) -> None:
        payload = {
            "sender": {
                "name": self.sender_name,
                "email": self.sender,
            },
            "to": [{"email": email}],
            "subject": "Codigo de recuperacion",
            "textContent": (
                "Solicitaste recuperar tu contrasena.\n\n"
                f"Tu codigo temporal es: {code}\n"
                "Este codigo vence en 15 minutos y solo puede utilizarse una vez.\n"
                "Si no solicitaste este correo, ignoralo."
            ),
        }
        request = Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "accept": "application/json",
                "api-key": self.api_key,
                "content-type": "application/json",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
                if response.status < 200 or response.status >= 300 or not isinstance(body, dict):
                    raise RecoveryCodeDeliveryError(
                        "El proveedor de correo devolvio una respuesta invalida."
                    )
        except RecoveryCodeDeliveryError:
            raise
        except (
            HTTPError,
            TimeoutError,
            URLError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            raise RecoveryCodeDeliveryError(
                "No se pudo enviar el codigo de recuperacion."
            ) from error
