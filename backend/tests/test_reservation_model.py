from datetime import UTC, datetime

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import RelationshipProperty

from app.core.database import Base
from app.models import Reservation, SportsSpace, User


def create_reservation(
    *,
    reservation_id: int = 1,
    user_id: int = 5,
    sports_space_id: int = 8,
    status: str = "confirmed",
    cancelled_at: datetime | None = None,
) -> Reservation:
    """
    Construye una reserva reutilizable sin utilizar PostgreSQL.

    El objeto permite comprobar los atributos y relaciones del modelo
    antes de implementar el repositorio y las reglas de negocio.
    """
    start_at = datetime(
        2026,
        11,
        2,
        18,
        0,
        tzinfo=UTC,
    )
    end_at = datetime(
        2026,
        11,
        2,
        19,
        0,
        tzinfo=UTC,
    )
    audit_time = datetime(
        2026,
        10,
        27,
        12,
        0,
        tzinfo=UTC,
    )

    return Reservation(
        id=reservation_id,
        user_id=user_id,
        sports_space_id=sports_space_id,
        start_at=start_at,
        end_at=end_at,
        status=status,
        cancelled_at=cancelled_at,
        created_at=audit_time,
        updated_at=audit_time,
    )


def test_reservation_model_is_registered_in_metadata() -> None:
    """
    Verifica que SQLAlchemy reconozca la tabla reservations.

    El registro dentro de Base.metadata tambien permite que Alembic
    detecte el modelo durante la generacion de migraciones.
    """
    assert "reservations" in Base.metadata.tables
    assert Reservation.__table__ is Base.metadata.tables["reservations"]


def test_reservation_model_contains_expected_columns() -> None:
    """
    Verifica las columnas persistentes necesarias para una reserva.
    """
    column_names = set(
        Reservation.__table__.columns.keys(),
    )

    assert column_names == {
        "id",
        "user_id",
        "sports_space_id",
        "start_at",
        "end_at",
        "status",
        "cancelled_at",
        "created_at",
        "updated_at",
    }


def test_reservation_required_columns_do_not_allow_null_values() -> None:
    """
    Verifica que los datos principales sean obligatorios.
    """
    required_columns = (
        Reservation.__table__.columns.user_id,
        Reservation.__table__.columns.sports_space_id,
        Reservation.__table__.columns.start_at,
        Reservation.__table__.columns.end_at,
        Reservation.__table__.columns.status,
        Reservation.__table__.columns.created_at,
        Reservation.__table__.columns.updated_at,
    )

    for column in required_columns:
        assert column.nullable is False


def test_reservation_cancelled_at_allows_null_value() -> None:
    """
    Verifica que una reserva confirmada no necesite fecha de cancelacion.
    """
    cancelled_at_column = Reservation.__table__.columns.cancelled_at

    assert cancelled_at_column.nullable is True


def test_reservation_status_has_confirmed_default() -> None:
    """
    Verifica el estado inicial administrado por Python y PostgreSQL.
    """
    status_column = Reservation.__table__.columns.status

    assert status_column.default is not None
    assert status_column.default.arg == "confirmed"
    assert status_column.server_default is not None
    assert str(status_column.server_default.arg) == "confirmed"


def test_reservation_has_foreign_key_to_user() -> None:
    """
    Verifica la relacion persistente con el usuario propietario.
    """
    foreign_keys = Reservation.__table__.columns.user_id.foreign_keys

    assert len(foreign_keys) == 1

    foreign_key = next(iter(foreign_keys))

    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "RESTRICT"


def test_reservation_has_foreign_key_to_sports_space() -> None:
    """
    Verifica la relacion persistente con el espacio reservado.
    """
    foreign_keys = Reservation.__table__.columns.sports_space_id.foreign_keys

    assert len(foreign_keys) == 1

    foreign_key = next(iter(foreign_keys))

    assert foreign_key.target_fullname == "sports_spaces.id"
    assert foreign_key.ondelete == "RESTRICT"


def test_reservation_filter_columns_are_indexed() -> None:
    """
    Verifica los indices previstos para consultas de reservas.

    Los indices permiten consultar por usuario, espacio, fecha de
    inicio y estado sin recorrer innecesariamente toda la tabla.
    """
    indexes = {
        tuple(column.name for column in index.columns) for index in Reservation.__table__.indexes
    }

    assert ("user_id",) in indexes
    assert ("sports_space_id",) in indexes
    assert ("start_at",) in indexes
    assert ("status",) in indexes


def test_reservation_requires_end_after_start() -> None:
    """
    Verifica que la finalizacion sea posterior al inicio.
    """
    check_constraints = [
        constraint
        for constraint in Reservation.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    constraint = next(
        constraint
        for constraint in check_constraints
        if constraint.name == "ck_reservations_end_after_start"
    )

    assert str(constraint.sqltext) == "end_at > start_at"


def test_reservation_limits_available_status_values() -> None:
    """
    Verifica que PostgreSQL limite los estados permitidos.
    """
    check_constraints = [
        constraint
        for constraint in Reservation.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    constraint = next(
        constraint
        for constraint in check_constraints
        if constraint.name == "ck_reservations_valid_status"
    )

    assert str(constraint.sqltext) == ("status IN ('confirmed', 'cancelled')")


def test_reservation_requires_consistent_cancellation_data() -> None:
    """
    Verifica la coherencia entre estado y fecha de cancelacion.
    """
    check_constraints = [
        constraint
        for constraint in Reservation.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    constraint = next(
        constraint
        for constraint in check_constraints
        if constraint.name == "ck_reservations_cancellation_consistency"
    )

    constraint_text = str(constraint.sqltext)

    assert "status = 'confirmed'" in constraint_text
    assert "cancelled_at IS NULL" in constraint_text
    assert "status = 'cancelled'" in constraint_text
    assert "cancelled_at IS NOT NULL" in constraint_text


def test_reservation_has_bidirectional_user_relationship() -> None:
    """
    Verifica la relacion bidireccional entre usuario y reserva.
    """
    reservation_relationship = Reservation.__mapper__.relationships["user"]
    user_relationship = User.__mapper__.relationships["reservations"]

    assert isinstance(
        reservation_relationship,
        RelationshipProperty,
    )
    assert reservation_relationship.mapper.class_ is User
    assert reservation_relationship.back_populates == "reservations"

    assert isinstance(
        user_relationship,
        RelationshipProperty,
    )
    assert user_relationship.mapper.class_ is Reservation
    assert user_relationship.back_populates == "user"
    assert user_relationship.uselist is True


def test_reservation_has_bidirectional_sports_space_relationship() -> None:
    """
    Verifica la relacion entre espacio deportivo y reserva.
    """
    reservation_relationship = Reservation.__mapper__.relationships["sports_space"]
    sports_space_relationship = SportsSpace.__mapper__.relationships["reservations"]

    assert isinstance(
        reservation_relationship,
        RelationshipProperty,
    )
    assert reservation_relationship.mapper.class_ is SportsSpace
    assert reservation_relationship.back_populates == "reservations"

    assert isinstance(
        sports_space_relationship,
        RelationshipProperty,
    )
    assert sports_space_relationship.mapper.class_ is Reservation
    assert sports_space_relationship.back_populates == "sports_space"
    assert sports_space_relationship.uselist is True


def test_reservation_does_not_store_static_availability() -> None:
    """
    Verifica que la disponibilidad no se guarde como columna.

    Los horarios disponibles se calcularan utilizando las reservas
    confirmadas, la sede, el espacio y la fecha seleccionada.
    """
    column_names = set(
        Reservation.__table__.columns.keys(),
    )

    assert "is_available" not in column_names
    assert "availability" not in column_names
    assert "available" not in column_names


def test_reservation_can_be_created_as_python_object() -> None:
    """
    Verifica la construccion de una reserva confirmada.
    """
    reservation = create_reservation()

    assert reservation.id == 1
    assert reservation.user_id == 5
    assert reservation.sports_space_id == 8
    assert reservation.start_at == datetime(
        2026,
        11,
        2,
        18,
        0,
        tzinfo=UTC,
    )
    assert reservation.end_at == datetime(
        2026,
        11,
        2,
        19,
        0,
        tzinfo=UTC,
    )
    assert reservation.status == "confirmed"
    assert reservation.cancelled_at is None


def test_cancelled_reservation_can_preserve_cancellation_time() -> None:
    """
    Verifica la representacion de una reserva cancelada.
    """
    cancellation_time = datetime(
        2026,
        10,
        30,
        10,
        15,
        tzinfo=UTC,
    )

    reservation = create_reservation(
        status="cancelled",
        cancelled_at=cancellation_time,
    )

    assert reservation.status == "cancelled"
    assert reservation.cancelled_at == cancellation_time
