from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class PushDevice(Base):
    """
    Representa una instalacion registrada para recibir notificaciones.

    Un usuario puede utilizar la aplicacion desde varios dispositivos.
    Cada registro conserva el identificador entregado por Firebase y
    la plataforma desde la que se realizo el registro.
    """

    # Nombre fisico de la tabla dentro de PostgreSQL.
    __tablename__ = "push_devices"

    # Identificador interno generado automaticamente.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Usuario propietario de la instalacion.
    #
    # La eliminacion fisica del usuario elimina tambien sus dispositivos
    # porque estos registros no forman parte del historial funcional.
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Identificador unico entregado por Firebase para esta instalacion.
    #
    # El indice permite localizar rapidamente una instalacion existente
    # cuando Firebase vuelve a informar el mismo identificador.
    installation_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    # Plataforma desde la que se registra la instalacion.
    #
    # Los valores iniciales esperados son android, ios o web.
    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Permite desactivar una instalacion sin eliminarla fisicamente.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Fecha y hora del primer registro de la instalacion.
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

    # Usuario propietario de la instalacion.
    user: Mapped[User] = relationship(
        back_populates="push_devices",
    )
