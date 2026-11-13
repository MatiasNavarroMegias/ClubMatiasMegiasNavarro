from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_firebase_user
from app.models import User
from app.repositories import UserRepository
from app.services import FirebaseIdentity


def create_user(
    *,
    firebase_uid: str = "firebase-uid",
    is_active: bool = True,
) -> User:
    return User(
        id=7,
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email="user@example.com",
        password_hash=None,
        firebase_uid=firebase_uid,
        is_active=is_active,
    )


def test_current_firebase_user_uses_validated_uid() -> None:
    database_session = MagicMock(spec=Session)
    user = create_user()
    database_session.scalar.return_value = user

    result = get_current_firebase_user(
        database_session,
        FirebaseIdentity("firebase-uid", "user@example.com", True),
    )

    assert result is user
    statement = database_session.scalar.call_args.args[0]
    assert "firebase-uid" in statement.compile().params.values()


def test_current_firebase_user_rejects_unknown_uid() -> None:
    database_session = MagicMock(spec=Session)
    database_session.scalar.return_value = None

    with pytest.raises(HTTPException) as raised:
        get_current_firebase_user(
            database_session,
            FirebaseIdentity("unknown", "user@example.com", True),
        )

    assert raised.value.status_code == 401


def test_current_firebase_user_rejects_inactive_user() -> None:
    database_session = MagicMock(spec=Session)
    database_session.scalar.return_value = create_user(is_active=False)

    with pytest.raises(HTTPException) as raised:
        get_current_firebase_user(
            database_session,
            FirebaseIdentity("firebase-uid", "user@example.com", True),
        )

    assert raised.value.status_code == 403


def test_current_firebase_user_does_not_use_user_id_lookup() -> None:
    database_session = MagicMock(spec=Session)
    database_session.scalar.return_value = create_user()
    repository = UserRepository(database_session)

    result = repository.get_by_firebase_uid("firebase-uid")

    assert result is database_session.scalar.return_value
    database_session.get.assert_not_called()
