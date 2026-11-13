import logging
from dataclasses import dataclass
from typing import Protocol

from firebase_admin import auth

from app.services.firebase_admin_app import FirebaseAdminAppProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FirebaseIdentity:
    """Identidad minima extraida de un Firebase ID Token validado."""

    uid: str
    email: str
    email_verified: bool


class FirebaseIdentityVerificationError(Exception):
    """Indica que un Firebase ID Token no puede autenticar una solicitud."""

    def __init__(self, code: str) -> None:
        super().__init__("No se pudo validar la identidad de Firebase.")
        self.code = code


class FirebaseIdentityVerifier(Protocol):
    """Abstraccion para validar identidades emitidas por Firebase."""

    def verify(self, id_token: str) -> FirebaseIdentity:
        """Valida un ID Token y devuelve su identidad confiable."""


class FirebaseAdminIdentityVerifier:
    """Valida Firebase ID Tokens mediante Firebase Admin SDK."""

    def __init__(
        self,
        *,
        app_provider: FirebaseAdminAppProvider,
        check_revoked: bool = True,
    ) -> None:
        self.app_provider = app_provider
        self.check_revoked = check_revoked

    def verify(self, id_token: str) -> FirebaseIdentity:
        if not id_token.strip():
            raise FirebaseIdentityVerificationError("invalid")

        try:
            firebase_app = self.app_provider.get_app()
            claims = auth.verify_id_token(
                id_token,
                app=firebase_app,
                check_revoked=self.check_revoked,
            )
        except auth.ExpiredIdTokenError as error:
            self._raise_known_error("expired", error)
        except auth.RevokedIdTokenError as error:
            self._raise_known_error("revoked", error)
        except auth.UserDisabledError as error:
            self._raise_known_error("disabled", error)
        except auth.CertificateFetchError as error:
            self._raise_known_error("certificate", error)
        except auth.InvalidIdTokenError as error:
            self._raise_known_error("invalid", error)

        uid = claims.get("uid")
        email = claims.get("email")
        email_verified = claims.get("email_verified", False)

        if (
            not isinstance(uid, str)
            or not uid.strip()
            or not isinstance(email, str)
            or not email.strip()
            or not isinstance(email_verified, bool)
        ):
            raise FirebaseIdentityVerificationError("invalid")

        return FirebaseIdentity(
            uid=uid,
            email=email.strip().lower(),
            email_verified=email_verified,
        )

    @staticmethod
    def _raise_known_error(code: str, error: Exception) -> None:
        logger.info("Falló la validación de identidad Firebase: %s.", code)
        raise FirebaseIdentityVerificationError(code) from error
