from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models import PasswordRecoveryToken
from app.repositories import PasswordRecoveryRepository


def create_recovery_token(
    token_id=1,
    user_id=7,
    failed_attempts=0,
    used_at=None,
):
    """
    Construye un codigo de recuperacion reutilizable.

    El objeto se crea en memoria y no se persiste en PostgreSQL.
    """
    created_at = datetime(
        2026,
        10,
        29,
        15,
        0,
        tzinfo=UTC,
    )

    return PasswordRecoveryToken(
        id=token_id,
        user_id=user_id,
        code_digest="a" * 64,
        expires_at=created_at + timedelta(minutes=15),
        used_at=used_at,
        failed_attempts=failed_attempts,
        created_at=created_at,
    )


def create_repository():
    """
    Construye el repositorio con una sesion simulada.
    """
    database_session = MagicMock(
        spec=Session,
    )

    repository = PasswordRecoveryRepository(
        database_session,
    )

    return repository, database_session


def test_password_recovery_repository_uses_database_session():
    """
    Verifica que el repositorio conserve la sesion recibida.
    """
    repository, database_session = create_repository()

    assert repository.database_session is database_session


def test_add_persists_and_refreshes_recovery_token():
    """
    Verifica la persistencia de un nuevo codigo.
    """
    repository, database_session = create_repository()
    recovery_token = create_recovery_token()

    result = repository.add(
        recovery_token,
    )

    assert result is recovery_token

    database_session.add.assert_called_once_with(
        recovery_token,
    )
    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(
        recovery_token,
    )


def test_get_latest_unused_by_user_returns_token():
    """
    Verifica la devolucion del codigo sin usar mas reciente.
    """
    repository, database_session = create_repository()
    expected_token = create_recovery_token()

    database_session.scalar.return_value = expected_token

    result = repository.get_latest_unused_by_user(
        user_id=7,
    )

    assert result is expected_token
    database_session.scalar.assert_called_once()


def test_get_latest_unused_by_user_returns_none():
    """
    Verifica el resultado cuando no existe un codigo disponible.
    """
    repository, database_session = create_repository()

    database_session.scalar.return_value = None

    result = repository.get_latest_unused_by_user(
        user_id=999,
    )

    assert result is None
    database_session.scalar.assert_called_once()


def test_get_latest_unused_by_user_builds_expected_query():
    """
    Verifica el usuario, estado y orden utilizados en la consulta.
    """
    repository, database_session = create_repository()

    repository.get_latest_unused_by_user(
        user_id=7,
    )

    statement = database_session.scalar.call_args.args[0]
    compiled_statement = statement.compile()

    statement_text = str(compiled_statement).upper()
    parameters = compiled_statement.params

    assert "PASSWORD_RECOVERY_TOKENS.USER_ID" in statement_text
    assert "PASSWORD_RECOVERY_TOKENS.USED_AT IS NULL" in statement_text
    assert "PASSWORD_RECOVERY_TOKENS.CREATED_AT DESC" in statement_text
    assert "PASSWORD_RECOVERY_TOKENS.ID DESC" in statement_text
    assert "LIMIT" in statement_text
    assert 7 in parameters.values()
    assert 1 in parameters.values()


def test_invalidate_unused_by_user_updates_and_commits():
    """
    Verifica la invalidacion de codigos anteriores.
    """
    repository, database_session = create_repository()

    invalidated_at = datetime(
        2026,
        10,
        29,
        15,
        10,
        tzinfo=UTC,
    )

    execution_result = MagicMock()
    execution_result.rowcount = 2
    database_session.execute.return_value = execution_result

    invalidated_count = repository.invalidate_unused_by_user(
        user_id=7,
        invalidated_at=invalidated_at,
    )

    assert invalidated_count == 2

    database_session.execute.assert_called_once()
    database_session.commit.assert_called_once_with()

    statement = database_session.execute.call_args.args[0]
    compiled_statement = statement.compile()

    statement_text = str(compiled_statement).upper()
    parameters = compiled_statement.params

    assert "UPDATE PASSWORD_RECOVERY_TOKENS" in statement_text
    assert "PASSWORD_RECOVERY_TOKENS.USER_ID" in statement_text
    assert "PASSWORD_RECOVERY_TOKENS.USED_AT IS NULL" in statement_text
    assert 7 in parameters.values()
    assert invalidated_at in parameters.values()


def test_invalidate_unused_by_user_returns_zero_without_matches():
    """
    Verifica una invalidacion sin codigos anteriores.
    """
    repository, database_session = create_repository()

    execution_result = MagicMock()
    execution_result.rowcount = 0
    database_session.execute.return_value = execution_result

    result = repository.invalidate_unused_by_user(
        user_id=7,
        invalidated_at=datetime(
            2026,
            10,
            29,
            15,
            10,
            tzinfo=UTC,
        ),
    )

    assert result == 0
    database_session.commit.assert_called_once_with()


def test_save_confirms_and_refreshes_recovery_token():
    """
    Verifica la persistencia de cambios sobre un codigo.
    """
    repository, database_session = create_repository()

    recovery_token = create_recovery_token(
        failed_attempts=3,
    )

    result = repository.save(
        recovery_token,
    )

    assert result is recovery_token
    assert result.failed_attempts == 3

    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(
        recovery_token,
    )


def test_save_preserves_used_datetime():
    """
    Verifica la persistencia de la fecha de uso.
    """
    repository, database_session = create_repository()

    used_at = datetime(
        2026,
        10,
        29,
        15,
        8,
        tzinfo=UTC,
    )

    recovery_token = create_recovery_token(
        used_at=used_at,
    )

    result = repository.save(
        recovery_token,
    )

    assert result.used_at == used_at

    database_session.commit.assert_called_once_with()
    database_session.refresh.assert_called_once_with(
        recovery_token,
    )
