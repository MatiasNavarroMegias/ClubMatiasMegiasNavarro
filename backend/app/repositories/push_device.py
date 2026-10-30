from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PushDevice


class PushDeviceRepository:
    """
    Administra la persistencia de instalaciones para notificaciones.

    El repositorio concentra las consultas SQLAlchemy relacionadas
    con dispositivos push y no implementa reglas de negocio.
    """

    def __init__(self, database_session: Session) -> None:
        """
        Inicializa el repositorio con una sesion de SQLAlchemy.

        Args:
            database_session: Sesion utilizada para consultar y
                persistir instalaciones en PostgreSQL.
        """
        self.database_session = database_session

    def get_by_installation_id(
        self,
        installation_id: str,
    ) -> PushDevice | None:
        """
        Busca una instalacion mediante el identificador de Firebase.

        Args:
            installation_id: Identificador unico entregado por
                Firebase para una instalacion de la aplicacion.

        Returns:
            La instalacion encontrada o None cuando no existe.
        """
        statement = select(PushDevice).where(PushDevice.installation_id == installation_id)

        return self.database_session.scalar(statement)

    def add(
        self,
        push_device: PushDevice,
    ) -> PushDevice:
        """
        Persiste una instalacion y recupera los valores generados.

        Args:
            push_device: Instalacion que sera asociada con un usuario.

        Returns:
            Instalacion actualizada con identificador y fechas.
        """
        self.database_session.add(push_device)
        self.database_session.commit()
        self.database_session.refresh(push_device)

        return push_device

    def save(
        self,
        push_device: PushDevice,
    ) -> PushDevice:
        """
        Confirma los cambios de una instalacion existente.

        Args:
            push_device: Instalacion modificada por el servicio.

        Returns:
            Instalacion actualizada con los valores confirmados por
            PostgreSQL.
        """
        self.database_session.commit()
        self.database_session.refresh(push_device)

        return push_device
