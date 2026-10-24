from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.venue import Venue


class SportsSpace(Base):
    """
    Representa un espacio deportivo perteneciente a una sede.

    Cada espacio posee un tipo de deporte, un numero y un nombre
    visible. La disponibilidad no se almacena porque se calculara
    posteriormente mediante los horarios y las reservas existentes.
    """

    __tablename__ = "sports_spaces"

    __table_args__ = (
        UniqueConstraint(
            "venue_id",
            "sport_type",
            "space_number",
            name="uq_sports_spaces_venue_sport_number",
        ),
        CheckConstraint(
            "space_number > 0",
            name="ck_sports_spaces_space_number_positive",
        ),
    )

    # Identificador interno generado por PostgreSQL.
    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    # Identificador de la sede a la que pertenece el espacio.
    #
    # index=True facilita listar espacios filtrados por sede.
    # ondelete=RESTRICT evita eliminar una sede que todavia posee
    # espacios deportivos asociados.
    venue_id: Mapped[int] = mapped_column(
        ForeignKey(
            "venues.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # Nombre visible del espacio.
    #
    # Ejemplos:
    # - Cancha de Futbol 1
    # - Cancha de Tenis 2
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Tipo de deporte utilizado para filtros.
    #
    # Se almacena como texto para permitir incorporar nuevos deportes
    # sin modificar una enumeracion dentro de PostgreSQL.
    sport_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Numero que diferencia espacios del mismo deporte dentro de la sede.
    space_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    # Permite desactivar el espacio sin eliminar su historial.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Fecha y hora de creacion.
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

    # Sede asociada al espacio deportivo.
    venue: Mapped[Venue] = relationship(
        back_populates="sports_spaces",
    )
