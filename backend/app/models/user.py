from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.reservation import Reservation


class User(Base):
    """
    Representa una persona registrada dentro de la aplicacion.

    El modelo almacena los datos del perfil y la informacion necesaria
    para autenticar al usuario sin guardar su contrasena en texto plano.
    """

    # Nombre fisico de la tabla dentro de PostgreSQL.
    __tablename__ = "users"

    # Identificador interno generado automaticamente.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Nombre del usuario mostrado dentro de su perfil.
    first_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Apellido del usuario mostrado dentro de su perfil.
    last_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Fecha de nacimiento requerida por el perfil.
    birth_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Correo utilizado como identificador durante el inicio de sesion.
    #
    # unique evita registrar dos cuentas con el mismo correo.
    # index permite optimizar la busqueda durante la autenticacion.
    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
        index=True,
    )

    # Resultado del algoritmo de hashing aplicado a la contrasena.
    #
    # La contrasena original nunca debe guardarse en PostgreSQL.
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Permite desactivar una cuenta sin eliminar su perfil ni reservas.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Fecha y hora en que se creo la cuenta.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Fecha y hora de la ultima modificacion del perfil.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Reservas creadas por el usuario.
    #
    # No se configura eliminacion en cascada porque el historial debe
    # conservarse incluso si la cuenta queda inactiva.
    reservations: Mapped[list[Reservation]] = relationship(
        back_populates="user",
    )
