import json
import logging
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from app.services.recovery_notifier import (
    BrevoRecoveryCodeNotifier,
    RecoveryCodeDeliveryError,
    SMTPRecoveryCodeNotifier,
)


def test_smtp_notifier_sends_code_with_tls_and_authentication() -> None:
    notifier = SMTPRecoveryCodeNotifier(
        host="smtp.example.com",
        port=587,
        username="smtp-user",
        password="smtp-password",
        sender="no-reply@example.com",
        use_tls=True,
    )
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp

    with patch("app.services.recovery_notifier.smtplib.SMTP", return_value=smtp):
        notifier.send_recovery_code("user@example.com", "48392175")

    smtp.starttls.assert_called_once_with()
    smtp.login.assert_called_once_with("smtp-user", "smtp-password")
    smtp.send_message.assert_called_once()
    message = smtp.send_message.call_args.args[0]
    assert message["To"] == "user@example.com"
    assert "48392175" in message.get_content()


def test_brevo_notifier_sends_exact_payload_and_api_key() -> None:
    notifier = BrevoRecoveryCodeNotifier(
        api_key="secret-api-key",
        sender="verified@example.com",
        sender_name="Club Matias Megias Navarro",
        api_url="https://api.brevo.test/v3/smtp/email",
    )
    response = MagicMock(status=201)
    response.read.return_value = b'{"messageId":"accepted"}'
    response.__enter__.return_value = response

    with patch(
        "app.services.recovery_notifier.urlopen",
        return_value=response,
    ) as open_url:
        notifier.send_recovery_code("user@example.com", "48392175")

    request = open_url.call_args.args[0]
    assert request.get_header("Api-key") == "secret-api-key"
    assert json.loads(request.data) == {
        "sender": {
            "name": "Club Matias Megias Navarro",
            "email": "verified@example.com",
        },
        "to": [{"email": "user@example.com"}],
        "subject": "Codigo de recuperacion",
        "textContent": (
            "Solicitaste recuperar tu contrasena.\n\n"
            "Tu codigo temporal es: 48392175\n"
            "Este codigo vence en 15 minutos y solo puede utilizarse una vez.\n"
            "Si no solicitaste este correo, ignoralo."
        ),
    }


@pytest.mark.parametrize(
    "error",
    [
        TimeoutError(),
        OSError("network"),
        ValueError("invalid"),
        HTTPError("https://brevo.test", 400, "bad request", {}, None),
        HTTPError("https://brevo.test", 401, "unauthorized", {}, None),
        HTTPError("https://brevo.test", 429, "rate limited", {}, None),
        HTTPError("https://brevo.test", 500, "server error", {}, None),
        HTTPError("https://brevo.test", 599, "server error", {}, None),
    ],
)
def test_brevo_notifier_converts_transport_and_response_errors(error) -> None:
    notifier = BrevoRecoveryCodeNotifier(
        api_key="secret-api-key",
        sender="verified@example.com",
        sender_name="Club Matias Megias Navarro",
        api_url="https://api.brevo.test/v3/smtp/email",
    )

    with patch(
        "app.services.recovery_notifier.urlopen",
        side_effect=error,
    ):
        with pytest.raises(RecoveryCodeDeliveryError):
            notifier.send_recovery_code("user@example.com", "48392175")


def test_brevo_notifier_does_not_log_api_key_or_code(caplog) -> None:
    notifier = BrevoRecoveryCodeNotifier(
        api_key="secret-api-key",
        sender="verified@example.com",
        sender_name="Club Matias Megias Navarro",
        api_url="https://api.brevo.test/v3/smtp/email",
    )

    with (
        caplog.at_level(logging.DEBUG),
        patch(
            "app.services.recovery_notifier.urlopen",
            side_effect=OSError("network"),
        ),
    ):
        with pytest.raises(RecoveryCodeDeliveryError):
            notifier.send_recovery_code("user@example.com", "48392175")

    assert "secret-api-key" not in caplog.text
    assert "48392175" not in caplog.text


def test_brevo_notifier_rejects_invalid_json_response() -> None:
    notifier = BrevoRecoveryCodeNotifier(
        api_key="secret-api-key",
        sender="verified@example.com",
        sender_name="Club Matias Megias Navarro",
        api_url="https://api.brevo.test/v3/smtp/email",
    )
    response = MagicMock(status=201)
    response.read.return_value = b"not-json"
    response.__enter__.return_value = response

    with patch("app.services.recovery_notifier.urlopen", return_value=response):
        with pytest.raises(RecoveryCodeDeliveryError):
            notifier.send_recovery_code("user@example.com", "48392175")
