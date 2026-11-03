from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_auth_service, get_current_user
from app.main import app
from app.models import User
from app.repositories import UserRepository
from app.schemas import UserUpdate
from app.services import AuthService


def create_user() -> User:
    """
    Construye un usuario reutilizable para las pruebas del perfil.

    El objeto no se persiste en PostgreSQL y utiliza un hash ficticio.
    """
    audit_time = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)

    return User(
        id=7,
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email="matias@example.com",
        password_hash="$argon2id$hash-de-prueba",
        is_active=True,
        created_at=audit_time,
        updated_at=audit_time,
    )


@pytest.fixture
def profile_api() -> tuple[TestClient, User, MagicMock]:
    """
    Crea un cliente HTTP con usuario y servicio simulados.

    Las dependencias reemplazadas permiten probar la capa HTTP sin
    consultar PostgreSQL ni validar un JWT real.
    """
    user = create_user()
    service = MagicMock(spec=AuthService)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_auth_service] = lambda: service

    client = TestClient(app)

    yield client, user, service

    app.dependency_overrides.clear()


def test_user_update_accepts_and_normalizes_partial_data() -> None:
    """
    Verifica que el esquema acepte una actualizacion parcial.
    """
    update_data = UserUpdate(
        first_name=" Matias Actualizado ",
    )

    assert update_data.model_dump(exclude_unset=True) == {
        "first_name": "Matias Actualizado",
    }


def test_user_update_rejects_email_change() -> None:
    """
    Verifica que el correo no forme parte del perfil editable.
    """
    with pytest.raises(ValueError):
        UserUpdate(
            email="otro@example.com",
        )


def test_user_update_rejects_protected_fields() -> None:
    """
    Verifica que no puedan modificarse campos internos de la cuenta.
    """
    protected_fields = (
        {"id": 99},
        {"password_hash": "otro-hash"},
        {"is_active": False},
    )

    for protected_data in protected_fields:
        with pytest.raises(ValueError):
            UserUpdate(**protected_data)


def test_user_update_rejects_current_birth_date() -> None:
    """
    Verifica que la fecha de nacimiento sea anterior al dia actual.
    """
    with pytest.raises(
        ValueError,
        match="debe ser anterior al dia actual",
    ):
        UserUpdate(
            birth_date=date.today(),
        )


def test_user_update_rejects_name_with_only_spaces() -> None:
    """
    Verifica que el nombre no pueda contener solamente espacios.
    """
    with pytest.raises(
        ValueError,
        match="no pueden contener solo espacios",
    ):
        UserUpdate(
            first_name="   ",
        )


def test_update_profile_applies_only_received_changes() -> None:
    """
    Verifica la actualizacion parcial en la capa de servicio.
    """
    repository = MagicMock(spec=UserRepository)
    repository.save.side_effect = lambda user: user

    service = AuthService(
        repository=repository,
        password_hasher=MagicMock(),
    )
    user = create_user()

    result = service.update_profile(
        user=user,
        update_data=UserUpdate(
            first_name="Matias Actualizado",
        ),
    )

    assert result is user
    assert result.first_name == "Matias Actualizado"
    assert result.last_name == "Megias Navarro"
    assert result.birth_date == date(2000, 1, 15)
    assert result.email == "matias@example.com"

    repository.save.assert_called_once_with(user)


def test_update_profile_rejects_empty_request() -> None:
    """
    Verifica que la solicitud contenga al menos un campo.
    """
    repository = MagicMock(spec=UserRepository)
    service = AuthService(
        repository=repository,
        password_hasher=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="Debe indicar al menos un campo",
    ):
        service.update_profile(
            user=create_user(),
            update_data=UserUpdate(),
        )

    repository.save.assert_not_called()


def test_update_profile_rejects_unchanged_values() -> None:
    """
    Verifica que no se ejecute persistencia sin cambios reales.
    """
    repository = MagicMock(spec=UserRepository)
    service = AuthService(
        repository=repository,
        password_hasher=MagicMock(),
    )
    user = create_user()

    with pytest.raises(
        ValueError,
        match="coinciden con el perfil actual",
    ):
        service.update_profile(
            user=user,
            update_data=UserUpdate(
                first_name="Matias",
            ),
        )

    repository.save.assert_not_called()


def test_user_repository_save_commits_and_refreshes_user() -> None:
    """
    Verifica la persistencia de cambios sobre un usuario existente.
    """
    database_session = MagicMock()
    repository = UserRepository(database_session)
    user = create_user()

    result = repository.save(user)

    assert result is user
    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(user)


def test_update_my_profile_returns_updated_public_data(
    profile_api: tuple[TestClient, User, MagicMock],
) -> None:
    """
    Verifica la respuesta exitosa del endpoint PATCH.
    """
    client, user, service = profile_api

    updated_user = create_user()
    updated_user.first_name = "Matias Actualizado"
    service.update_profile.return_value = updated_user

    response = client.patch(
        "/users/me",
        headers={
            "Authorization": "Bearer token-de-prueba",
        },
        json={
            "first_name": "Matias Actualizado",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["first_name"] == "Matias Actualizado"
    assert response_data["last_name"] == "Megias Navarro"
    assert response_data["email"] == "matias@example.com"

    assert "password" not in response_data
    assert "password_hash" not in response_data

    service.update_profile.assert_called_once()

    call_arguments = service.update_profile.call_args.kwargs

    assert call_arguments["user"] is user
    assert call_arguments["update_data"].first_name == ("Matias Actualizado")


def test_update_my_profile_returns_400_without_changes(
    profile_api: tuple[TestClient, User, MagicMock],
) -> None:
    """
    Verifica la traduccion del error de negocio a HTTP 400.
    """
    client, _, service = profile_api
    service.update_profile.side_effect = ValueError(
        "Los datos enviados coinciden con el perfil actual."
    )

    response = client.patch(
        "/users/me",
        headers={
            "Authorization": "Bearer token-de-prueba",
        },
        json={
            "first_name": "Matias",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Los datos enviados coinciden con el perfil actual.",
    }


def test_update_my_profile_returns_422_for_email_change(
    profile_api: tuple[TestClient, User, MagicMock],
) -> None:
    """
    Verifica que intentar modificar el correo sea rechazado.
    """
    client, _, service = profile_api

    response = client.patch(
        "/users/me",
        headers={
            "Authorization": "Bearer token-de-prueba",
        },
        json={
            "email": "otro@example.com",
        },
    )

    assert response.status_code == 422
    service.update_profile.assert_not_called()


def test_update_my_profile_returns_401_without_token() -> None:
    """
    Verifica que la actualizacion requiera una sesion autenticada.
    """
    app.dependency_overrides.clear()
    client = TestClient(app)

    response = client.patch(
        "/users/me",
        json={
            "first_name": "Matias Actualizado",
        },
    )

    assert response.status_code == 401


def test_user_update_rejects_explicit_null_name() -> None:
    """
    Verifica que un nombre enviado explicitamente como null sea rechazado.

    El campo puede omitirse en un PATCH, pero no puede almacenarse como
    null porque la columna correspondiente es obligatoria.
    """
    with pytest.raises(
        ValueError,
        match="no pueden ser nulos",
    ):
        UserUpdate(
            first_name=None,
        )


def test_user_update_rejects_explicit_null_birth_date() -> None:
    """
    Verifica que una fecha enviada explicitamente como null sea rechazada.
    """
    with pytest.raises(
        ValueError,
        match="fecha de nacimiento no puede ser nula",
    ):
        UserUpdate(
            birth_date=None,
        )
