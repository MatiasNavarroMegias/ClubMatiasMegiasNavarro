from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_firebase_identity,
    get_firebase_profile_service,
)
from app.main import app
from app.models import User
from app.repositories import UserRepository
from app.schemas import FirebaseProfileCreate
from app.services import (
    FirebaseIdentity,
    FirebaseProfileConflictError,
    FirebaseProfileService,
    InactiveUserError,
)


def create_profile_data() -> FirebaseProfileCreate:
    return FirebaseProfileCreate(
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
    )


def create_user(
    *,
    firebase_uid: str | None = None,
    email: str = "user@example.com",
    is_active: bool = True,
) -> User:
    return User(
        id=7,
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email=email,
        password_hash=None if firebase_uid else "$argon2id$legacy",
        firebase_uid=firebase_uid,
        is_active=is_active,
        created_at=datetime(2026, 11, 3, tzinfo=UTC),
        updated_at=datetime(2026, 11, 3, tzinfo=UTC),
    )


def test_complete_profile_creates_user_from_token_identity() -> None:
    repository = MagicMock(spec=UserRepository)
    repository.get_by_firebase_uid.return_value = None
    repository.get_by_email.return_value = None
    repository.add.side_effect = lambda user: user
    service = FirebaseProfileService(repository)
    identity = FirebaseIdentity("firebase-uid", "claimed@example.com", True)

    user = service.complete_profile(
        identity=identity,
        profile_data=create_profile_data(),
    )

    assert user.firebase_uid == "firebase-uid"
    assert user.email == "claimed@example.com"
    assert user.password_hash is None
    repository.get_by_email.assert_called_once_with("claimed@example.com")
    repository.add.assert_called_once_with(user)


def test_complete_profile_is_idempotent_for_same_uid() -> None:
    repository = MagicMock(spec=UserRepository)
    existing_user = create_user(firebase_uid="firebase-uid")
    repository.get_by_firebase_uid.return_value = existing_user
    service = FirebaseProfileService(repository)

    result = service.complete_profile(
        identity=FirebaseIdentity("firebase-uid", "claimed@example.com", True),
        profile_data=create_profile_data(),
    )

    assert result is existing_user
    repository.get_by_email.assert_not_called()
    repository.add.assert_not_called()


def test_complete_profile_does_not_accept_identity_from_body() -> None:
    profile_data = create_profile_data()

    with pytest.raises(ValueError):
        FirebaseProfileCreate(
            **profile_data.model_dump(),
            firebase_uid="forged-uid",
            user_id=999,
        )


def test_complete_profile_rejects_legacy_email_without_linking() -> None:
    repository = MagicMock(spec=UserRepository)
    repository.get_by_firebase_uid.return_value = None
    repository.get_by_email.return_value = create_user()
    service = FirebaseProfileService(repository)

    with pytest.raises(FirebaseProfileConflictError):
        service.complete_profile(
            identity=FirebaseIdentity("firebase-uid", "user@example.com", True),
            profile_data=create_profile_data(),
        )

    repository.add.assert_not_called()


def test_complete_profile_rejects_inactive_firebase_user() -> None:
    repository = MagicMock(spec=UserRepository)
    repository.get_by_firebase_uid.return_value = create_user(
        firebase_uid="firebase-uid",
        is_active=False,
    )
    service = FirebaseProfileService(repository)

    with pytest.raises(InactiveUserError):
        service.complete_profile(
            identity=FirebaseIdentity("firebase-uid", "user@example.com", True),
            profile_data=create_profile_data(),
        )


def test_firebase_profile_endpoint_uses_token_identity_and_is_idempotent() -> None:
    service = MagicMock(spec=FirebaseProfileService)
    user = create_user(firebase_uid="firebase-uid", email="claimed@example.com")
    service.complete_profile.return_value = user
    identity = FirebaseIdentity("firebase-uid", "claimed@example.com", True)
    app.dependency_overrides[get_firebase_identity] = lambda: identity
    app.dependency_overrides[get_firebase_profile_service] = lambda: service

    try:
        response = TestClient(app).post(
            "/users/profile",
            headers={"Authorization": "Bearer firebase-id-token"},
            json={
                "first_name": "Matias",
                "last_name": "Megias Navarro",
                "birth_date": "2000-01-15",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["email"] == "claimed@example.com"
    service.complete_profile.assert_called_once()
    assert service.complete_profile.call_args.kwargs["identity"] is identity
