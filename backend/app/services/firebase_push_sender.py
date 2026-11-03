from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging


class FirebasePushSender:
    """Envia mensajes FCM dirigidos por Firebase Installation ID."""

    def __init__(
        self,
        *,
        credentials_path: str | None,
        project_id: str | None = None,
        app_name: str = "club_matias_megias_navarro",
    ) -> None:
        self.credentials_path = credentials_path
        self.project_id = project_id
        self.app_name = app_name

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
        try:
            return firebase_admin.get_app(self.app_name)
        except ValueError as error:
            if not self.credentials_path:
                raise RuntimeError("FIREBASE_CREDENTIALS_PATH no esta configurada.") from error

            credentials_file = Path(self.credentials_path)
            if not credentials_file.is_file():
                raise RuntimeError(
                    "No se encontro el archivo de credenciales de Firebase."
                ) from error

            certificate = credentials.Certificate(str(credentials_file))
            options = {"projectId": self.project_id} if self.project_id else None
            return firebase_admin.initialize_app(
                certificate,
                options=options,
                name=self.app_name,
            )
