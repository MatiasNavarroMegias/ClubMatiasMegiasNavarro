from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.sports_space import SportsSpace
    from app.models.user import User


class Reservation(Base):
    """
    Representa la reserva de un espacio deportivo por un usuario.

    Cada reserva conserva el horario de inicio y finalizacion, su
    estado y la fecha de cancelacion cuando corresponda.

    La disponibilidad no se almacena como una columna. Se calculara
    utilizando las reservas confirmadas del espacio seleccionado.
    """

    __tablename__ = "reservations"

    __table_args__ = (
        CheckConstraint(
            "end_at > start_at",
            name="ck_reservations_end_after_start",
        ),
        CheckConstraint(
            "status IN ('confirmed', 'cancelled')",
            name="ck_reservations_valid_status",
        ),
        CheckConstraint(
            (
                "(status = 'confirmed' AND cancelled_at IS NULL) OR "
                "(status = 'cancelled' AND cancelled_at IS NOT NULL)"
            ),
            name="ck_reservations_cancellation_consistency",
        ),
    )

    # Identificador interno generado automaticamente por PostgreSQL.
    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    # Usuario propietario de la reserva.
    #
    # RESTRICT evita eliminar usuarios con historial de reservas.
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # Espacio deportivo reservado.
    #
    # RESTRICT conserva la referencia historica aunque el espacio
    # posteriormente quede inactivo.
    sports_space_id: Mapped[int] = mapped_column(
        ForeignKey(
            "sports_spaces.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # Fecha y hora de inicio del turno.
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Fecha y hora de finalizacion del turno.
    #
    # El servicio validara que sea exactamente una hora posterior al
    # inicio. PostgreSQL garantiza como minimo que sea posterior.
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Estado actual de la reserva.
    #
    # confirmed representa una reserva vigente.
    # cancelled representa una cancelacion logica.
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="confirmed",
        server_default="confirmed",
        index=True,
    )

    # Fecha y hora de la cancelacion.
    #
    # Permanece en None mientras la reserva se encuentre confirmada.
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Fecha y hora de creacion del registro.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Fecha y hora de la ultima modificacion.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Usuario propietario de la reserva.
    user: Mapped[User] = relationship(
        back_populates="reservations",
    )

    # Espacio deportivo asociado a la reserva.
    sports_space: Mapped[SportsSpace] = relationship(
        back_populates="reservations",
    )
