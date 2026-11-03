from datetime import time

from sqlalchemy import String

from app.core.database import Base
from app.models import Venue


def test_venue_model_is_registered_in_metadata() -> None:
    """
    Verifica que SQLAlchemy registre el modelo Venue.

    Alembic utiliza Base.metadata para detectar los modelos y generar
    las futuras migraciones de la base de datos.
    """
    assert Venue.__tablename__ == "venues"
    assert "venues" in Base.metadata.tables


def test_venue_model_contains_expected_columns() -> None:
    """
    Verifica que la tabla logica contenga las columnas necesarias.

    Esta prueba protege la estructura basica del modelo ante cambios
    accidentales realizados durante el desarrollo.
    """
    expected_columns = {
        "id",
        "name",
        "address",
        "opening_time",
        "closing_time",
        "is_active",
        "created_at",
        "updated_at",
    }

    actual_columns = set(Venue.__table__.columns.keys())

    assert actual_columns == expected_columns


def test_venue_required_columns_do_not_allow_null_values() -> None:
    """
    Verifica que los datos obligatorios no permitan valores nulos.

    Las restricciones del modelo complementan las validaciones que
    posteriormente se agregaran mediante esquemas Pydantic.
    """
    required_columns = (
        Venue.__table__.columns.name,
        Venue.__table__.columns.address,
        Venue.__table__.columns.opening_time,
        Venue.__table__.columns.closing_time,
        Venue.__table__.columns.is_active,
        Venue.__table__.columns.created_at,
        Venue.__table__.columns.updated_at,
    )

    assert all(column.nullable is False for column in required_columns)


def test_venue_text_columns_have_expected_lengths() -> None:
    """
    Verifica los limites definidos para nombre y direccion.

    Estos limites tambien se utilizaran mas adelante en los esquemas
    de entrada para validar datos antes de enviarlos a PostgreSQL.
    """
    name_type = Venue.__table__.columns.name.type
    address_type = Venue.__table__.columns.address.type

    assert isinstance(name_type, String)
    assert isinstance(address_type, String)
    assert name_type.length == 100
    assert address_type.length == 200


def test_venue_can_be_created_as_python_object() -> None:
    """
    Verifica que una sede pueda construirse como objeto de Python.

    Esta prueba no guarda informacion en PostgreSQL. Solamente valida
    que SQLAlchemy asigne correctamente los valores recibidos.
    """
    venue = Venue(
        name="Sede Ramos Mejia",
        address="Avenida de Mayo 1000",
        opening_time=time(8, 0),
        closing_time=time(23, 0),
        is_active=True,
    )

    assert venue.name == "Sede Ramos Mejia"
    assert venue.address == "Avenida de Mayo 1000"
    assert venue.opening_time == time(8, 0)
    assert venue.closing_time == time(23, 0)
    assert venue.is_active is True
