from unittest.mock import MagicMock, patch

from app.services.firebase_push_sender import FirebasePushSender


def test_sender_targets_firebase_installation_id() -> None:
    messaging = MagicMock()
    message = object()
    app = object()
    messaging.Message.return_value = message
    sender = FirebasePushSender(credentials_path="firebase-admin-key.json")

    with (
        patch(
            "app.services.firebase_push_sender.messaging",
            messaging,
        ),
        patch.object(sender, "_get_app", return_value=app),
    ):
        sender.send(
            installation_id="fid-1",
            title="Reserva confirmada",
            body="Mensaje",
        )

    messaging.Message.assert_called_once()
    message_kwargs = messaging.Message.call_args.kwargs
    assert message_kwargs["fid"] == "fid-1"
    messaging.Notification.assert_called_once_with(
        title="Reserva confirmada",
        body="Mensaje",
    )
    messaging.send.assert_called_once_with(message, app=app)
