from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class PasswordRecoveryToken(Base):
    """
    Representa un codigo temporal para recuperar una contrasena.

    El codigo original nunca se guarda en PostgreSQL. Solamente se
    persiste un resumen HMAC generado con una clave secreta del
    servidor.

    Cada registro posee fecha de vencimiento, cantidad de intentos
    fallidos y una fecha de uso opcional para garantizar que el codigo
    pueda utilizarse una sola vez.
    """

    __tablename__ = "password_recovery_tokens"

    __table_args__ = (
        CheckConstraint(
            "failed_attempts >= 0",
            name="ck_password_recovery_tokens_non_negative_attempts",
        ),
    )

    # Identificador interno generado por PostgreSQL.
    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    # Usuario propietario del codigo de recuperacion.
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Resumen HMAC del codigo enviado al usuario.
    #
    # SHA-256 produce 64 caracteres cuando se representa en formato
    # hexadecimal.
    code_digest: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    # Momento hasta el cual el codigo puede utilizarse.
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Momento en que el codigo fue utilizado correctamente.
    #
    # Un valor distinto de null impide reutilizar el mismo codigo.
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Cantidad de verificaciones incorrectas realizadas.
    failed_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # Momento en que se genero el codigo.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Usuario asociado con el codigo de recuperacion.
    user: Mapped[User] = relationship(
        back_populates="password_recovery_tokens",
    )
