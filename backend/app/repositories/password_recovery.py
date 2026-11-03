from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import PasswordRecoveryToken


class PasswordRecoveryRepository:
    """
    Administra la persistencia de codigos de recuperacion.

    El repositorio concentra las consultas SQLAlchemy y no decide si
    un codigo esta vencido, bloqueado o coincide con el valor enviado
    por el usuario. Esas reglas pertenecen al servicio.
    """

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        """
        Inicializa el repositorio con una sesion de SQLAlchemy.

        Args:
            database_session: Sesion asociada con la operacion actual.
        """
        self.database_session = database_session

    def add(
        self,
        recovery_token: PasswordRecoveryToken,
    ) -> PasswordRecoveryToken:
        """
        Persiste un nuevo codigo de recuperacion.

        Args:
            recovery_token: Codigo protegido que debe guardarse.

        Returns:
            Registro actualizado con identificador y fechas.
        """
        self.database_session.add(
            recovery_token,
        )
        self.database_session.commit()
        self.database_session.refresh(
            recovery_token,
        )

        return recovery_token

    def get_latest_unused_by_user(
        self,
        user_id: int,
    ) -> PasswordRecoveryToken | None:
        """
        Obtiene el codigo sin usar mas reciente del usuario.

        La consulta no filtra por vencimiento ni cantidad de intentos.
        Esas reglas dependen del momento actual y se verifican dentro
        del servicio de recuperacion.

        Args:
            user_id: Identificador del usuario propietario.

        Returns:
            Codigo mas reciente sin utilizar o None.
        """
        statement = (
            select(PasswordRecoveryToken)
            .where(
                PasswordRecoveryToken.user_id == user_id,
                PasswordRecoveryToken.used_at.is_(None),
            )
            .order_by(
                PasswordRecoveryToken.created_at.desc(),
                PasswordRecoveryToken.id.desc(),
            )
            .limit(1)
        )

        return self.database_session.scalar(
            statement,
        )

    def invalidate_unused_by_user(
        self,
        *,
        user_id: int,
        invalidated_at: datetime,
    ) -> int:
        """
        Invalida los codigos anteriores sin utilizar.

        La fecha de uso tambien funciona como fecha de invalidacion.
        Esto garantiza que solamente el codigo generado mas
        recientemente pueda utilizarse.

        Args:
            user_id: Identificador del usuario propietario.
            invalidated_at: Momento exacto de la invalidacion.

        Returns:
            Cantidad de registros invalidados.
        """
        statement = (
            update(PasswordRecoveryToken)
            .where(
                PasswordRecoveryToken.user_id == user_id,
                PasswordRecoveryToken.used_at.is_(None),
            )
            .values(
                used_at=invalidated_at,
            )
        )

        result = self.database_session.execute(
            statement,
        )
        self.database_session.commit()

        return result.rowcount or 0

    def save(
        self,
        recovery_token: PasswordRecoveryToken,
    ) -> PasswordRecoveryToken:
        """
        Confirma cambios sobre un codigo existente.

        Se utiliza para guardar intentos fallidos o marcar un codigo
        como utilizado correctamente.

        Args:
            recovery_token: Registro modificado por el servicio.

        Returns:
            Codigo actualizado con los valores confirmados.
        """
        self.database_session.commit()
        self.database_session.refresh(
            recovery_token,
        )

        return recovery_token
