import firebase_admin
from firebase_admin import messaging

from app.services.firebase_admin_app import FirebaseAdminAppProvider


class FirebasePushSender:
    """Envia mensajes FCM dirigidos por Firebase Installation ID."""

    def __init__(
        self,
        *,
        credentials_path: str | None,
        project_id: str | None = None,
        app_provider: FirebaseAdminAppProvider | None = None,
    ) -> None:
        self.app_provider = app_provider or FirebaseAdminAppProvider(
            credentials_path=credentials_path,
            project_id=project_id,
        )

    def send(
        self,
        *,
        installation_id: str,
        title: str,
        body: str,
    ) -> None:
        app = self._get_app()
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            android=messaging.AndroidConfig(priority="high"),
            fid=installation_id,
        )
        messaging.send(message, app=app)

    def _get_app(self) -> firebase_admin.App:
        return self.app_provider.get_app()
