from unittest.mock import MagicMock, patch

import pytest

from app.services.firebase_admin_app import (
    FirebaseAdminAppProvider,
    FirebaseAdminConfigurationError,
)


def test_provider_initializes_default_app_once(tmp_path) -> None:
    credentials_path = tmp_path / "firebase-admin-key.json"
    credentials_path.write_text("{}", encoding="utf-8")
    firebase_app = object()
    provider = FirebaseAdminAppProvider(
        credentials_path=str(credentials_path),
        project_id="club-project",
    )

    with (
        patch(
            "app.services.firebase_admin_app.firebase_admin.get_app",
            side_effect=[ValueError("missing"), ValueError("missing"), firebase_app],
        ),
        patch(
            "app.services.firebase_admin_app.credentials.Certificate",
            return_value=object(),
        ) as certificate,
        patch(
            "app.services.firebase_admin_app.firebase_admin.initialize_app",
            return_value=firebase_app,
        ) as initialize,
    ):
        assert provider.get_app() is firebase_app
        assert provider.get_app() is firebase_app

    certificate.assert_called_once_with(str(credentials_path))
    initialize.assert_called_once()


def test_provider_reuses_existing_default_app_without_initializing() -> None:
    firebase_app = object()
    provider = FirebaseAdminAppProvider(credentials_path=None)

    with (
        patch(
            "app.services.firebase_admin_app.firebase_admin.get_app",
            return_value=firebase_app,
        ),
        patch(
            "app.services.firebase_admin_app.firebase_admin.initialize_app",
        ) as initialize,
    ):
        assert provider.get_app() is firebase_app

    initialize.assert_not_called()


@pytest.mark.parametrize(
    ("credentials_path", "message"),
    [
        (None, "FIREBASE_CREDENTIALS_PATH"),
        ("missing.json", "No se encontro"),
    ],
)
def test_provider_rejects_missing_credentials(
    credentials_path: str | None,
    message: str,
) -> None:
    provider = FirebaseAdminAppProvider(credentials_path=credentials_path)

    with pytest.raises(FirebaseAdminConfigurationError, match=message):
        provider.get_app()


def test_identity_and_push_sender_can_share_provider() -> None:
    provider = MagicMock()
    firebase_app = object()
    provider.get_app.return_value = firebase_app

    from app.services.firebase_identity import FirebaseAdminIdentityVerifier
    from app.services.firebase_push_sender import FirebasePushSender

    identity_verifier = FirebaseAdminIdentityVerifier(app_provider=provider)
    push_sender = FirebasePushSender(
        credentials_path=None,
        app_provider=provider,
    )

    with (
        patch(
            "app.services.firebase_identity.auth.verify_id_token",
            return_value={
                "uid": "firebase-user",
                "email": "user@example.com",
                "email_verified": True,
            },
        ) as verify,
        patch(
            "app.services.firebase_push_sender.messaging",
        ),
    ):
        identity_verifier.verify("firebase-id-token")
        push_sender.send(
            installation_id="fid",
            title="Titulo",
            body="Mensaje",
        )

    verify.assert_called_once_with(
        "firebase-id-token",
        app=firebase_app,
        check_revoked=True,
    )
    assert provider.get_app.call_count == 2
