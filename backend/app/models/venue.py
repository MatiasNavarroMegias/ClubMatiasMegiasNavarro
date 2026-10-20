from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Venue(Base):
    """
    Representa una sede deportiva almacenada en PostgreSQL.

    El modelo contiene la informacion general necesaria para mostrar
    una sede y validar que las futuras reservas se encuentren dentro
    de su horario de funcionamiento.
    """

    # Nombre fisico de la tabla dentro de PostgreSQL.
    __tablename__ = "venues"

    # Identificador interno generado automaticamente por PostgreSQL.
    #
    # primary_key establece que el valor identifica de forma unica
    # cada registro y permite que SQLAlchemy lo utilice en consultas.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Nombre visible de la sede.
    #
    # index=True crea un indice que facilitara busquedas por nombre.
    # nullable=False impide guardar una sede sin nombre.
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # Direccion fisica utilizada para mostrar y localizar la sede.
    address: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # Horario de inicio de las actividades de la sede.
    opening_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    # Horario de finalizacion de las actividades de la sede.
    closing_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    # Permite desactivar una sede sin eliminar su informacion.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Fecha y hora en que se creo el registro.
    #
    # server_default delega el valor inicial a PostgreSQL.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Fecha y hora de la ultima modificacion.
    #
    # onupdate actualiza el valor cuando SQLAlchemy modifica el objeto.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
