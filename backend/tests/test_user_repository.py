from datetime import date
from unittest.mock import ANY, MagicMock

from sqlalchemy.orm import Session

from app.models import User
from app.repositories import UserRepository


def create_user(
    email: str = "matias@example.com",
) -> User:
    """
    Crea un usuario reutilizable para las pruebas del repositorio.

    El objeto contiene un hash ficticio y nunca una contrasena real.
    La funcion no persiste informacion dentro de PostgreSQL.
    """
    return User(
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email=email,
        password_hash="$argon2id$hash-de-prueba",
        is_active=True,
    )


def test_get_by_email_returns_existing_user() -> None:
    """
    Verifica que el repositorio devuelva el usuario encontrado.

    La sesion se simula para evitar una consulta real a PostgreSQL.
    """
    database_session = MagicMock(spec=Session)
    expected_user = create_user()
    database_session.scalar.return_value = expected_user

    repository = UserRepository(database_session)

    user = repository.get_by_email("matias@example.com")

    assert user is expected_user
    database_session.scalar.assert_called_once_with(ANY)


def test_get_by_email_builds_query_with_received_email() -> None:
    """
    Verifica que la consulta utilice el correo recibido.

    La representacion SQL compilada permite comprobar el criterio
    sin ejecutar la consulta contra PostgreSQL.
    """
    database_session = MagicMock(spec=Session)
    repository = UserRepository(database_session)

    repository.get_by_email("matias@example.com")

    statement = database_session.scalar.call_args.args[0]
    compiled_statement = statement.compile()
    query_parameters = compiled_statement.params

    assert "matias@example.com" in query_parameters.values()


def test_get_by_email_returns_none_when_user_does_not_exist() -> None:
    """
    Verifica que el repositorio devuelva None para un correo inexistente.

    La decision de convertir este resultado en un error de negocio
    pertenecera al servicio de autenticacion.
    """
    database_session = MagicMock(spec=Session)
    database_session.scalar.return_value = None

    repository = UserRepository(database_session)

    user = repository.get_by_email("unknown@example.com")

    assert user is None
    database_session.scalar.assert_called_once_with(ANY)


def test_add_persists_and_refreshes_user() -> None:
    """
    Verifica que add agregue, confirme y recargue el usuario.

    refresh recupera los valores generados por PostgreSQL, como el
    identificador y las fechas de auditoria.
    """
    database_session = MagicMock(spec=Session)
    user = create_user()

    repository = UserRepository(database_session)

    result = repository.add(user)

    assert result is user
    database_session.add.assert_called_once_with(user)
    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(user)


def test_repository_only_receives_user_with_password_hash() -> None:
    """
    Verifica que el objeto persistido no contenga una contrasena directa.

    El repositorio debe recibir un modelo cuyo hash fue generado
    previamente por el servicio de autenticacion.
    """
    database_session = MagicMock(spec=Session)
    user = create_user()

    repository = UserRepository(database_session)

    repository.add(user)

    persisted_user = database_session.add.call_args.args[0]

    assert persisted_user.password_hash == "$argon2id$hash-de-prueba"
    assert not hasattr(persisted_user, "password")
    assert not hasattr(persisted_user, "plain_password")


def test_get_by_id_returns_existing_user() -> None:
    """
    Verifica que el repositorio devuelva el usuario identificado.
    """
    database_session = MagicMock(spec=Session)
    expected_user = create_user()
    database_session.get.return_value = expected_user

    repository = UserRepository(database_session)

    user = repository.get_by_id(7)

    assert user is expected_user
    database_session.get.assert_called_once_with(User, 7)


def test_get_by_id_returns_none_when_user_does_not_exist() -> None:
    """
    Verifica que un identificador inexistente produzca None.

    La dependencia de autenticacion decidira posteriormente como
    convertir este resultado en una respuesta HTTP.
    """
    database_session = MagicMock(spec=Session)
    database_session.get.return_value = None

    repository = UserRepository(database_session)

    user = repository.get_by_id(999)

    assert user is None
    database_session.get.assert_called_once_with(User, 999)
