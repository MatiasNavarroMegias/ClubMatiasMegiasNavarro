import logging
from functools import lru_cache
from pathlib import Path
from threading import Lock

import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)


class FirebaseAdminConfigurationError(RuntimeError):
    """Indica que Firebase Admin no puede configurarse en el servidor."""


class FirebaseAdminAppProvider:
    """Obtiene o inicializa la aplicacion default de Firebase Admin."""

    def __init__(
        self,
        *,
        credentials_path: str | None,
        project_id: str | None = None,
    ) -> None:
        self.credentials_path = credentials_path
        self.project_id = project_id
        self._lock = Lock()

    def get_app(self) -> firebase_admin.App:
        try:
            return firebase_admin.get_app()
        except ValueError:
            pass

        with self._lock:
            try:
                return firebase_admin.get_app()
            except ValueError:
                app = self._initialize()
                logger.info("Firebase Admin inicializado por el provider compartido.")
                return app

    def _initialize(self) -> firebase_admin.App:
        if not self.credentials_path:
            raise FirebaseAdminConfigurationError("FIREBASE_CREDENTIALS_PATH no esta configurada.")

        credentials_file = Path(self.credentials_path)
        if not credentials_file.is_file():
            raise FirebaseAdminConfigurationError(
                "No se encontro el archivo de credenciales de Firebase."
            )

        try:
            certificate = credentials.Certificate(str(credentials_file))
            options = {"projectId": self.project_id} if self.project_id else None
            return firebase_admin.initialize_app(certificate, options=options)
        except (OSError, ValueError, TypeError) as error:
            logger.error("Firebase Admin no pudo inicializarse: configuracion invalida.")
            raise FirebaseAdminConfigurationError(
                "La configuracion de Firebase Admin no es valida."
            ) from error


@lru_cache
def get_firebase_admin_app_provider(
    credentials_path: str | None,
    project_id: str | None,
) -> FirebaseAdminAppProvider:
    """Devuelve el provider compartido para una configuracion."""
    return FirebaseAdminAppProvider(
        credentials_path=credentials_path,
        project_id=project_id,
    )
