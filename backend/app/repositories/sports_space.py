from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SportsSpace


class SportsSpaceRepository:
    """
    Administra la persistencia de los espacios deportivos.

    El repositorio concentra las consultas de SQLAlchemy y permite
    combinar filtros por sede, deporte y estado.
    """

    def __init__(self, database_session: Session) -> None:
        """
        Inicializa el repositorio con una sesion de SQLAlchemy.

        Args:
            database_session: Sesion utilizada para consultar y
                modificar informacion en PostgreSQL.
        """
        self.database_session = database_session

    def list_all(
        self,
        *,
        venue_id: int | None = None,
        sport_type: str | None = None,
        active_only: bool = False,
    ) -> list[SportsSpace]:
        """
        Devuelve los espacios que cumplen los filtros recibidos.

        Los filtros pueden utilizarse de forma individual o combinada.
        El orden facilita mostrar los espacios agrupados por deporte
        y numero dentro de la interfaz.

        Args:
            venue_id: Sede opcional utilizada como filtro.
            sport_type: Tipo deportivo opcional ya normalizado.
            active_only: Indica si deben excluirse espacios inactivos.

        Returns:
            Lista de espacios ordenada por deporte, numero y nombre.
        """
        statement = select(SportsSpace)

        if venue_id is not None:
            statement = statement.where(
                SportsSpace.venue_id == venue_id,
            )

        if sport_type is not None:
            statement = statement.where(
                SportsSpace.sport_type == sport_type,
            )

        if active_only:
            statement = statement.where(
                SportsSpace.is_active.is_(True),
            )

        statement = statement.order_by(
            SportsSpace.sport_type,
            SportsSpace.space_number,
            SportsSpace.name,
        )

        return list(
            self.database_session.scalars(statement).all(),
        )

    def get_by_id(
        self,
        sports_space_id: int,
    ) -> SportsSpace | None:
        """
        Busca un espacio deportivo mediante su clave primaria.

        Args:
            sports_space_id: Identificador interno del espacio.

        Returns:
            El espacio encontrado o None cuando no existe.
        """
        return self.database_session.get(
            SportsSpace,
            sports_space_id,
        )

    def get_by_identity(
        self,
        *,
        venue_id: int,
        sport_type: str,
        space_number: int,
    ) -> SportsSpace | None:
        """
        Busca un espacio mediante su identificacion dentro de la sede.

        Esta consulta permite detectar duplicados antes de intentar
        persistir un registro que violaria la restriccion unica.

        Args:
            venue_id: Identificador de la sede.
            sport_type: Tipo deportivo normalizado.
            space_number: Numero del espacio dentro del deporte.

        Returns:
            El espacio encontrado o None cuando no existe.
        """
        statement = select(SportsSpace).where(
            SportsSpace.venue_id == venue_id,
            SportsSpace.sport_type == sport_type,
            SportsSpace.space_number == space_number,
        )

        return self.database_session.scalar(statement)

    def add(
        self,
        sports_space: SportsSpace,
    ) -> SportsSpace:
        """
        Persiste un nuevo espacio deportivo.

        Args:
            sports_space: Instancia que debe agregarse.

        Returns:
            Espacio recargado con los valores generados por PostgreSQL.
        """
        self.database_session.add(sports_space)
        self.database_session.commit()
        self.database_session.refresh(sports_space)

        return sports_space

    def save(
        self,
        sports_space: SportsSpace,
    ) -> SportsSpace:
        """
        Confirma las modificaciones de un espacio existente.

        Args:
            sports_space: Espacio previamente obtenido y modificado.

        Returns:
            Espacio actualizado despues de confirmar la transaccion.
        """
        self.database_session.commit()
        self.database_session.refresh(sports_space)

        return sports_space
