from datetime import UTC, datetime, timedelta

from sqlalchemy import inspect
from sqlalchemy.orm import configure_mappers

from app.models import PasswordRecoveryToken, User


def create_token(
    *,
    user_id: int = 7,
    failed_attempts: int = 0,
    used_at: datetime | None = None,
) -> PasswordRecoveryToken:
    """
    Construye un codigo de recuperacion reutilizable.

    El codigo original no se almacena. code_digest representa el
    resumen HMAC que se persistira en PostgreSQL.
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
        id=1,
        user_id=user_id,
        code_digest="a" * 64,
        expires_at=created_at + timedelta(minutes=15),
        used_at=used_at,
        failed_attempts=failed_attempts,
        created_at=created_at,
    )


def test_password_recovery_token_uses_expected_table() -> None:
    """
    Verifica el nombre fisico de la tabla.
    """
    assert PasswordRecoveryToken.__tablename__ == "password_recovery_tokens"


def test_password_recovery_token_contains_expected_columns() -> None:
    """
    Verifica la estructura persistente del modelo.
    """
    assert list(PasswordRecoveryToken.__table__.columns.keys()) == [
        "id",
        "user_id",
        "code_digest",
        "expires_at",
        "used_at",
        "failed_attempts",
        "created_at",
    ]


def test_password_recovery_token_builds_valid_instance() -> None:
    """
    Verifica que el modelo conserve los datos recibidos.
    """
    token = create_token()

    assert token.id == 1
    assert token.user_id == 7
    assert token.code_digest == "a" * 64
    assert token.failed_attempts == 0
    assert token.used_at is None
    assert token.expires_at > token.created_at


def test_password_recovery_token_accepts_used_datetime() -> None:
    """
    Verifica que un codigo pueda marcarse como utilizado.
    """
    used_at = datetime(
        2026,
        10,
        29,
        15,
        5,
        tzinfo=UTC,
    )

    token = create_token(
        used_at=used_at,
    )

    assert token.used_at == used_at


def test_password_recovery_token_accepts_failed_attempts() -> None:
    """
    Verifica el registro de verificaciones incorrectas.
    """
    token = create_token(
        failed_attempts=4,
    )

    assert token.failed_attempts == 4


def test_password_recovery_token_has_user_foreign_key() -> None:
    """
    Verifica la referencia obligatoria hacia users.
    """
    user_id_column = PasswordRecoveryToken.__table__.columns["user_id"]
    foreign_key = next(iter(user_id_column.foreign_keys))

    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"
    assert user_id_column.nullable is False


def test_password_recovery_token_has_expected_indexes() -> None:
    """
    Verifica los indices utilizados por las consultas.
    """
    index_names = {index.name for index in PasswordRecoveryToken.__table__.indexes}

    assert index_names == {
        "ix_password_recovery_tokens_code_digest",
        "ix_password_recovery_tokens_expires_at",
        "ix_password_recovery_tokens_user_id",
    }


def test_password_recovery_token_has_attempt_constraint() -> None:
    """
    Verifica que los intentos no puedan ser negativos.
    """
    constraint_names = {
        constraint.name
        for constraint in PasswordRecoveryToken.__table__.constraints
        if constraint.name is not None
    }

    assert "ck_password_recovery_tokens_non_negative_attempts" in constraint_names


def test_password_recovery_token_relationships_are_configured() -> None:
    """
    Verifica las relaciones en ambos sentidos.
    """
    configure_mappers()

    assert "password_recovery_tokens" in User.__mapper__.relationships
    assert "user" in PasswordRecoveryToken.__mapper__.relationships


def test_password_recovery_token_mapper_uses_expected_model() -> None:
    """
    Verifica que SQLAlchemy inspeccione correctamente el modelo.
    """
    mapper = inspect(
        PasswordRecoveryToken,
    )

    assert mapper.class_ is PasswordRecoveryToken
    assert mapper.local_table.name == "password_recovery_tokens"
