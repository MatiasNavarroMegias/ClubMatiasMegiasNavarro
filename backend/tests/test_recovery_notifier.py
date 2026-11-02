from unittest.mock import MagicMock, patch

from app.services.recovery_notifier import SMTPRecoveryCodeNotifier


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
