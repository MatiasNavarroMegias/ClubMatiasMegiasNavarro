from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from firebase_admin import auth

from app.api.dependencies import get_firebase_identity
from app.services.firebase_admin_app import FirebaseAdminConfigurationError
from app.services.firebase_identity import (
    FirebaseAdminIdentityVerifier,
    FirebaseIdentity,
    FirebaseIdentityVerificationError,
)


def test_verifier_returns_typed_identity_from_validated_claims() -> None:
    firebase_app = object()
    provider = MagicMock()
    provider.get_app.return_value = firebase_app
    verifier = FirebaseAdminIdentityVerifier(app_provider=provider)

    with patch(
        "app.services.firebase_identity.auth.verify_id_token",
        return_value={
            "uid": "firebase-user-123",
            "email": "user@example.com",
            "email_verified": True,
        },
    ) as verify:
        identity = verifier.verify("firebase-id-token")

    verify.assert_called_once_with(
        "firebase-id-token",
        app=firebase_app,
        check_revoked=True,
    )
    assert identity == FirebaseIdentity(
        uid="firebase-user-123",
        email="user@example.com",
        email_verified=True,
    )


@pytest.mark.parametrize(
    ("firebase_error", "expected_code"),
    [
        (auth.ExpiredIdTokenError("expired", ValueError("cause")), "expired"),
        (auth.RevokedIdTokenError("revoked"), "revoked"),
        (auth.UserDisabledError("disabled"), "disabled"),
        (auth.InvalidIdTokenError("invalid"), "invalid"),
        (auth.CertificateFetchError("certificate", ValueError("cause")), "certificate"),
    ],
)
def test_verifier_translates_firebase_errors(
    firebase_error: Exception,
    expected_code: str,
) -> None:
    provider = MagicMock()
    provider.get_app.return_value = object()
    verifier = FirebaseAdminIdentityVerifier(app_provider=provider)

    with patch(
        "app.services.firebase_identity.auth.verify_id_token",
        side_effect=firebase_error,
    ):
        with pytest.raises(FirebaseIdentityVerificationError) as raised:
            verifier.verify("firebase-id-token")

    assert raised.value.code == expected_code


@pytest.mark.parametrize(
    "claims",
    [
        {},
        {"email": "user@example.com"},
        {"uid": "firebase-user-123"},
        {"uid": "firebase-user-123", "email": None},
    ],
)
def test_verifier_rejects_missing_identity_claims(claims: dict[str, object]) -> None:
    provider = MagicMock()
    provider.get_app.return_value = object()
    verifier = FirebaseAdminIdentityVerifier(app_provider=provider)

    with patch(
        "app.services.firebase_identity.auth.verify_id_token",
        return_value=claims,
    ):
        with pytest.raises(FirebaseIdentityVerificationError) as raised:
            verifier.verify("firebase-id-token")

    assert raised.value.code == "invalid"


def test_verifier_does_not_log_token_or_claims(caplog) -> None:
    provider = MagicMock()
    provider.get_app.return_value = object()
    verifier = FirebaseAdminIdentityVerifier(app_provider=provider)

    with patch(
        "app.services.firebase_identity.auth.verify_id_token",
        side_effect=auth.InvalidIdTokenError("invalid"),
    ):
        with pytest.raises(FirebaseIdentityVerificationError):
            verifier.verify("secret-firebase-id-token")

    assert "secret-firebase-id-token" not in caplog.text
    assert "user@example.com" not in caplog.text


def test_missing_firebase_admin_configuration_returns_service_unavailable() -> None:
    settings = MagicMock(
        firebase_credentials_path=None,
        firebase_project_id=None,
    )
    with (
        patch("app.api.dependencies.get_settings", return_value=settings),
        patch(
            "app.api.dependencies.get_firebase_admin_app_provider",
            side_effect=FirebaseAdminConfigurationError("missing"),
        ),
    ):
        with pytest.raises(HTTPException) as raised:
            get_firebase_identity(
                HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials="firebase-id-token",
                )
            )

    assert raised.value.status_code == 503
    assert raised.value.detail == "El servicio de autenticacion no esta disponible."


def test_invalid_firebase_token_remains_unauthorized() -> None:
    settings = MagicMock(
        firebase_credentials_path="firebase-admin-key.json",
        firebase_project_id="club-project",
    )
    provider = MagicMock()
    provider.get_app.return_value = object()
    with (
        patch("app.api.dependencies.get_settings", return_value=settings),
        patch(
            "app.api.dependencies.get_firebase_admin_app_provider",
            return_value=provider,
        ),
        patch(
            "app.services.firebase_identity.auth.verify_id_token",
            side_effect=auth.InvalidIdTokenError("invalid"),
        ),
    ):
        with pytest.raises(HTTPException) as raised:
            get_firebase_identity(
                HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials="altered-token",
                )
            )

    assert raised.value.status_code == 401
