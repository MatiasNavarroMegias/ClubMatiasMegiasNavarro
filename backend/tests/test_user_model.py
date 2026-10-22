from datetime import date

from sqlalchemy import Date, String

from app.core.database import Base
from app.models import User


def test_user_model_is_registered_in_metadata() -> None:
    """
    Verifica que SQLAlchemy registre el modelo User.

    Alembic utiliza Base.metadata para detectar el modelo y generar
    posteriormente la migracion de la tabla users.
    """
    assert User.__tablename__ == "users"
    assert "users" in Base.metadata.tables


def test_user_model_contains_expected_columns() -> None:
    """
    Verifica que la tabla logica contenga las columnas necesarias.

    Esta prueba protege la estructura del usuario ante modificaciones
    accidentales durante el desarrollo.
    """
    expected_columns = {
        "id",
        "first_name",
        "last_name",
        "birth_date",
        "email",
        "password_hash",
        "is_active",
        "created_at",
        "updated_at",
    }

    actual_columns = set(User.__table__.columns.keys())

    assert actual_columns == expected_columns


def test_user_required_columns_do_not_allow_null_values() -> None:
    """
    Verifica que los datos obligatorios no permitan valores nulos.

    Las restricciones del modelo complementaran las validaciones
    incorporadas posteriormente mediante esquemas Pydantic.
    """
    required_columns = (
        User.__table__.columns.first_name,
        User.__table__.columns.last_name,
        User.__table__.columns.birth_date,
        User.__table__.columns.email,
        User.__table__.columns.password_hash,
        User.__table__.columns.is_active,
        User.__table__.columns.created_at,
        User.__table__.columns.updated_at,
    )

    assert all(column.nullable is False for column in required_columns)


def test_user_text_columns_have_expected_lengths() -> None:
    """
    Verifica que los textos respeten los limites del modelo de datos.
    """
    first_name_type = User.__table__.columns.first_name.type
    last_name_type = User.__table__.columns.last_name.type
    email_type = User.__table__.columns.email.type
    password_hash_type = User.__table__.columns.password_hash.type

    assert isinstance(first_name_type, String)
    assert isinstance(last_name_type, String)
    assert isinstance(email_type, String)
    assert isinstance(password_hash_type, String)

    assert first_name_type.length == 50
    assert last_name_type.length == 50
    assert email_type.length == 320
    assert password_hash_type.length == 255


def test_user_birth_date_uses_date_type() -> None:
    """
    Verifica que la fecha de nacimiento no almacene hora.

    El perfil necesita una fecha, pero no una hora ni una zona horaria.
    """
    birth_date_type = User.__table__.columns.birth_date.type

    assert isinstance(birth_date_type, Date)


def test_user_email_is_unique_and_indexed() -> None:
    """
    Verifica las restricciones necesarias para identificar una cuenta.

    El correo debe ser unico y estar indexado porque se utilizara
    frecuentemente durante el inicio de sesion.
    """
    email_column = User.__table__.columns.email

    assert email_column.unique is True
    assert email_column.index is True


def test_user_model_does_not_store_plain_password() -> None:
    """
    Verifica que el modelo no posea una columna de contrasena directa.

    PostgreSQL debe conservar solamente password_hash y nunca la
    contrasena original recibida durante el registro.
    """
    column_names = set(User.__table__.columns.keys())

    assert "password_hash" in column_names
    assert "password" not in column_names
    assert "plain_password" not in column_names


def test_user_can_be_created_as_python_object() -> None:
    """
    Verifica que un usuario pueda construirse como objeto de Python.

    Esta prueba no guarda informacion en PostgreSQL. La persistencia
    fisica se habilitara posteriormente mediante una migracion.
    """
    user = User(
        first_name="Matias",
        last_name="Megias Navarro",
        birth_date=date(2000, 1, 15),
        email="matias@example.com",
        password_hash="password-hash-for-testing",
        is_active=True,
    )

    assert user.first_name == "Matias"
    assert user.last_name == "Megias Navarro"
    assert user.birth_date == date(2000, 1, 15)
    assert user.email == "matias@example.com"
    assert user.password_hash == "password-hash-for-testing"
    assert user.is_active is True
