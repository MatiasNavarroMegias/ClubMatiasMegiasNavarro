from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Venue


class VenueRepository:
    """
    Administra las operaciones de persistencia de las sedes.

    El repositorio concentra las consultas de SQLAlchemy para evitar
    que los endpoints y servicios accedan directamente a PostgreSQL.
    """

    def __init__(self, database_session: Session) -> None:
        """
        Inicializa el repositorio con una sesion de SQLAlchemy.

        Args:
            database_session: Sesion utilizada para consultar y
                modificar datos dentro de PostgreSQL.
        """
        self.database_session = database_session

    def list_all(self) -> list[Venue]:
        """
        Devuelve todas las sedes ordenadas alfabeticamente.

        Returns:
            Lista de sedes ordenada por nombre.
        """
        statement = select(Venue).order_by(Venue.name)

        return list(
            self.database_session.scalars(statement).all(),
        )

    def get_by_id(self, venue_id: int) -> Venue | None:
        """
        Busca una sede mediante su identificador.

        Args:
            venue_id: Identificador interno de la sede.

        Returns:
            La sede encontrada o None cuando no existe.
        """
        return self.database_session.get(Venue, venue_id)

    def add(self, venue: Venue) -> Venue:
        """
        Agrega una sede y confirma la transaccion.

        Args:
            venue: Instancia que debe persistirse.

        Returns:
            La sede actualizada con los valores generados por
            PostgreSQL, como el identificador y las fechas.
        """
        self.database_session.add(venue)
        self.database_session.commit()
        self.database_session.refresh(venue)

        return venue

    def save(self, venue: Venue) -> Venue:
        """
        Confirma las modificaciones realizadas sobre una sede.

        SQLAlchemy detecta los cambios efectuados en una instancia
        previamente obtenida mediante la misma sesion.

        Args:
            venue: Sede modificada que debe guardarse.

        Returns:
            La sede actualizada despues de confirmar la transaccion.
        """
        self.database_session.commit()
        self.database_session.refresh(venue)

        return venue
