from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import RelationshipProperty

from app.core.database import Base
from app.models import SportsSpace, Venue


def create_sports_space() -> SportsSpace:
    """
    Construye un espacio deportivo sin utilizar PostgreSQL.

    El objeto permite comprobar los atributos del modelo antes de
    persistirlo mediante el repositorio.
    """
    audit_time = datetime(2026, 10, 24, 13, 30, tzinfo=UTC)

    return SportsSpace(
        id=1,
        venue_id=7,
        name="Cancha de Futbol 1",
        sport_type="Futbol",
        space_number=1,
        is_active=True,
        created_at=audit_time,
        updated_at=audit_time,
    )


def test_sports_space_model_is_registered_in_metadata() -> None:
    """
    Verifica que SQLAlchemy reconozca la tabla sports_spaces.

    Esto tambien permite que Alembic detecte el modelo durante la
    generacion automatica de migraciones.
    """
    assert "sports_spaces" in Base.metadata.tables
    assert SportsSpace.__table__ is Base.metadata.tables["sports_spaces"]


def test_sports_space_model_contains_expected_columns() -> None:
    """
    Verifica las columnas necesarias para administrar un espacio.
    """
    column_names = set(SportsSpace.__table__.columns.keys())

    assert column_names == {
        "id",
        "venue_id",
        "name",
        "sport_type",
        "space_number",
        "is_active",
        "created_at",
        "updated_at",
    }


def test_sports_space_required_columns_do_not_allow_null_values() -> None:
    """
    Verifica que los datos principales sean obligatorios.
    """
    required_columns = (
        SportsSpace.__table__.columns.venue_id,
        SportsSpace.__table__.columns.name,
        SportsSpace.__table__.columns.sport_type,
        SportsSpace.__table__.columns.space_number,
        SportsSpace.__table__.columns.is_active,
        SportsSpace.__table__.columns.created_at,
        SportsSpace.__table__.columns.updated_at,
    )

    for column in required_columns:
        assert column.nullable is False


def test_sports_space_text_columns_have_expected_lengths() -> None:
    """
    Verifica que el modelo y los futuros esquemas compartan limites.
    """
    assert SportsSpace.__table__.columns.name.type.length == 100
    assert SportsSpace.__table__.columns.sport_type.type.length == 50


def test_sports_space_has_foreign_key_to_venue() -> None:
    """
    Verifica que cada espacio pertenezca a una sede.
    """
    foreign_keys = SportsSpace.__table__.columns.venue_id.foreign_keys

    assert len(foreign_keys) == 1

    foreign_key = next(iter(foreign_keys))

    assert foreign_key.target_fullname == "venues.id"
    assert foreign_key.ondelete == "RESTRICT"


def test_sports_space_filter_columns_are_indexed() -> None:
    """
    Verifica los indices utilizados para filtrar espacios.

    venue_id permite listar por sede y sport_type permite aplicar el
    filtro de deporte solicitado por el trabajo practico.
    """
    indexes = {
        tuple(column.name for column in index.columns) for index in SportsSpace.__table__.indexes
    }

    assert ("venue_id",) in indexes
    assert ("sport_type",) in indexes


def test_sports_space_has_unique_venue_sport_number_constraint() -> None:
    """
    Verifica que no se repita un numero para el mismo deporte y sede.
    """
    unique_constraints = [
        constraint
        for constraint in SportsSpace.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    expected_constraint = next(
        constraint
        for constraint in unique_constraints
        if constraint.name == "uq_sports_spaces_venue_sport_number"
    )

    constrained_columns = tuple(column.name for column in expected_constraint.columns)

    assert constrained_columns == (
        "venue_id",
        "sport_type",
        "space_number",
    )


def test_sports_space_requires_positive_space_number() -> None:
    """
    Verifica la restriccion que impide numeros nulos o negativos.
    """
    check_constraints = [
        constraint
        for constraint in SportsSpace.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    expected_constraint = next(
        constraint
        for constraint in check_constraints
        if constraint.name == "ck_sports_spaces_space_number_positive"
    )

    assert str(expected_constraint.sqltext) == "space_number > 0"


def test_sports_space_has_bidirectional_venue_relationship() -> None:
    """
    Verifica la relacion bidireccional entre sede y espacio.
    """
    sports_space_relationship = SportsSpace.__mapper__.relationships["venue"]
    venue_relationship = Venue.__mapper__.relationships["sports_spaces"]

    assert isinstance(
        sports_space_relationship,
        RelationshipProperty,
    )
    assert sports_space_relationship.mapper.class_ is Venue
    assert sports_space_relationship.back_populates == "sports_spaces"

    assert isinstance(
        venue_relationship,
        RelationshipProperty,
    )
    assert venue_relationship.mapper.class_ is SportsSpace
    assert venue_relationship.back_populates == "venue"
    assert venue_relationship.uselist is True


def test_sports_space_does_not_store_static_availability() -> None:
    """
    Verifica que la disponibilidad no se guarde como una columna.

    La disponibilidad se calculara utilizando horarios, reservas y la
    fecha seleccionada para evitar datos desactualizados.
    """
    column_names = set(SportsSpace.__table__.columns.keys())

    assert "is_available" not in column_names
    assert "availability" not in column_names
    assert "available" not in column_names


def test_sports_space_can_be_created_as_python_object() -> None:
    """
    Verifica la construccion del objeto antes de persistirlo.
    """
    sports_space = create_sports_space()

    assert sports_space.id == 1
    assert sports_space.venue_id == 7
    assert sports_space.name == "Cancha de Futbol 1"
    assert sports_space.sport_type == "Futbol"
    assert sports_space.space_number == 1
    assert sports_space.is_active is True
    assert sports_space.created_at == datetime(
        2026,
        10,
        24,
        13,
        30,
        tzinfo=UTC,
    )
    assert sports_space.updated_at == datetime(
        2026,
        10,
        24,
        13,
        30,
        tzinfo=UTC,
    )
