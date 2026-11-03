from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String

from app.core.database import Base
from app.models import PushDevice


def test_push_device_model_is_registered_in_metadata() -> None:
    """
    Verifica que SQLAlchemy registre el modelo PushDevice.

    Alembic utiliza Base.metadata para detectar el modelo y generar
    posteriormente la migracion de la tabla push_devices.
    """
    assert PushDevice.__tablename__ == "push_devices"
    assert "push_devices" in Base.metadata.tables


def test_push_device_model_contains_expected_columns() -> None:
    """
    Verifica que el modelo contenga las columnas necesarias.

    La instalacion se vincula con un usuario y conserva la informacion
    necesaria para administrar las notificaciones push.
    """
    expected_columns = {
        "id",
        "user_id",
        "installation_id",
        "platform",
        "is_active",
        "created_at",
        "updated_at",
    }

    actual_columns = set(PushDevice.__table__.columns.keys())

    assert actual_columns == expected_columns


def test_push_device_required_columns_do_not_allow_null_values() -> None:
    """
    Verifica que los datos obligatorios no permitan valores nulos.
    """
    required_columns = (
        PushDevice.__table__.columns.user_id,
        PushDevice.__table__.columns.installation_id,
        PushDevice.__table__.columns.platform,
        PushDevice.__table__.columns.is_active,
        PushDevice.__table__.columns.created_at,
        PushDevice.__table__.columns.updated_at,
    )

    assert all(column.nullable is False for column in required_columns)


def test_push_device_text_columns_have_expected_lengths() -> None:
    """
    Verifica los limites definidos para los campos de texto.

    El identificador de instalacion utiliza un limite amplio porque
    su formato es administrado por Firebase.
    """
    installation_id_type = PushDevice.__table__.columns.installation_id.type
    platform_type = PushDevice.__table__.columns.platform.type

    assert isinstance(installation_id_type, String)
    assert isinstance(platform_type, String)

    assert installation_id_type.length == 255
    assert platform_type.length == 20


def test_push_device_installation_id_is_unique_and_indexed() -> None:
    """
    Verifica que una instalacion no pueda registrarse dos veces.

    El indice tambien permite localizar rapidamente una instalacion
    cuando Firebase informa nuevamente el mismo identificador.
    """
    installation_id_column = PushDevice.__table__.columns.installation_id

    assert installation_id_column.unique is True
    assert installation_id_column.index is True


def test_push_device_user_id_references_users_table() -> None:
    """
    Verifica que cada instalacion pertenezca a un usuario.

    La clave foranea evita almacenar dispositivos asociados con
    cuentas inexistentes.
    """
    user_id_column = PushDevice.__table__.columns.user_id
    foreign_keys = list(user_id_column.foreign_keys)

    assert len(foreign_keys) == 1

    foreign_key = foreign_keys[0]

    assert isinstance(foreign_key, ForeignKey)
    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"


def test_push_device_uses_expected_column_types() -> None:
    """
    Verifica los tipos utilizados para estado y auditoria.
    """
    is_active_type = PushDevice.__table__.columns.is_active.type
    created_at_type = PushDevice.__table__.columns.created_at.type
    updated_at_type = PushDevice.__table__.columns.updated_at.type

    assert isinstance(is_active_type, Boolean)
    assert isinstance(created_at_type, DateTime)
    assert isinstance(updated_at_type, DateTime)

    assert created_at_type.timezone is True
    assert updated_at_type.timezone is True


def test_push_device_can_be_created_as_python_object() -> None:
    """
    Verifica que una instalacion pueda construirse sin persistencia.

    La prueba no utiliza PostgreSQL ni envia mensajes reales mediante
    Firebase.
    """
    push_device = PushDevice(
        user_id=7,
        installation_id="firebase-installation-id-for-testing",
        platform="android",
        is_active=True,
    )

    assert push_device.user_id == 7
    assert push_device.installation_id == "firebase-installation-id-for-testing"
    assert push_device.platform == "android"
    assert push_device.is_active is True


def test_push_device_audit_attributes_accept_datetime_values() -> None:
    """
    Verifica que los atributos de auditoria acepten fechas con hora.

    PostgreSQL normalmente completa estos valores mediante sus
    valores predeterminados cuando se persiste la instalacion.
    """
    audit_time = datetime.fromisoformat("2026-10-30T15:00:00+00:00")

    push_device = PushDevice(
        user_id=7,
        installation_id="another-installation-id",
        platform="android",
        is_active=True,
        created_at=audit_time,
        updated_at=audit_time,
    )

    assert push_device.created_at == audit_time
    assert push_device.updated_at == audit_time
