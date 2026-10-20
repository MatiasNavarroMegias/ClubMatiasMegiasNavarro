from datetime import time

from app.models import Venue
from app.repositories import VenueRepository
from app.schemas import VenueCreate, VenueUpdate


class VenueNotFoundError(Exception):
    """
    Indica que la sede solicitada no existe.

    El servicio utiliza una excepcion propia para no depender de
    FastAPI ni de codigos HTTP.
    """


class VenueNoChangesError(Exception):
    """
    Indica que la solicitud no contiene modificaciones efectivas.

    Esta excepcion evita confirmar una transaccion cuando todos los
    valores recibidos coinciden con los valores actuales de la sede.
    """


class InvalidVenueHoursError(Exception):
    """
    Indica que el horario final de la sede no es valido.

    Esta validacion es necesaria durante actualizaciones parciales,
    porque VenueUpdate puede recibir solamente uno de los horarios.
    """


class VenueService:
    """
    Aplica las reglas de negocio relacionadas con las sedes.

    El servicio coordina los esquemas de entrada, el modelo Venue
    y las operaciones de persistencia del repositorio.
    """

    def __init__(self, repository: VenueRepository) -> None:
        """
        Inicializa el servicio con un repositorio de sedes.

        Args:
            repository: Repositorio utilizado para consultar y
                modificar sedes.
        """
        self.repository = repository

    def list_venues(self) -> list[Venue]:
        """
        Devuelve todas las sedes disponibles en el repositorio.

        Returns:
            Lista de sedes ordenada por el repositorio.
        """
        return self.repository.list_all()

    def get_venue(self, venue_id: int) -> Venue:
        """
        Obtiene una sede mediante su identificador.

        Args:
            venue_id: Identificador interno de la sede.

        Returns:
            La sede encontrada.

        Raises:
            VenueNotFoundError: Cuando no existe una sede con el
                identificador recibido.
        """
        venue = self.repository.get_by_id(venue_id)

        if venue is None:
            raise VenueNotFoundError(f"No existe una sede con el identificador {venue_id}.")

        return venue

    def create_venue(self, venue_data: VenueCreate) -> Venue:
        """
        Crea y persiste una nueva sede.

        Los datos ya fueron validados por VenueCreate antes de llegar
        al servicio.

        Args:
            venue_data: Datos validados de la nueva sede.

        Returns:
            La sede persistida con sus valores generados.
        """
        venue = Venue(
            name=venue_data.name,
            address=venue_data.address,
            opening_time=venue_data.opening_time,
            closing_time=venue_data.closing_time,
            is_active=True,
        )

        return self.repository.add(venue)

    def update_venue(
        self,
        venue_id: int,
        venue_data: VenueUpdate,
    ) -> Venue:
        """
        Modifica parcialmente una sede existente.

        La operacion combina los campos recibidos con los valores
        actuales antes de validar el horario final.

        Args:
            venue_id: Identificador de la sede que debe actualizarse.
            venue_data: Campos enviados por la solicitud PATCH.

        Returns:
            La sede actualizada.

        Raises:
            VenueNotFoundError: Cuando la sede no existe.
            VenueNoChangesError: Cuando no se recibieron cambios
                efectivos.
            InvalidVenueHoursError: Cuando el horario final no es valido.
        """
        venue = self.get_venue(venue_id)

        changes = venue_data.model_dump(exclude_unset=True)

        if not changes:
            raise VenueNoChangesError("La solicitud no contiene campos para modificar.")

        effective_changes = {
            field_name: new_value
            for field_name, new_value in changes.items()
            if getattr(venue, field_name) != new_value
        }

        if not effective_changes:
            raise VenueNoChangesError("Los valores recibidos coinciden con los datos actuales.")

        opening_time = effective_changes.get(
            "opening_time",
            venue.opening_time,
        )
        closing_time = effective_changes.get(
            "closing_time",
            venue.closing_time,
        )

        self._validate_operating_hours(
            opening_time=opening_time,
            closing_time=closing_time,
        )

        for field_name, new_value in effective_changes.items():
            setattr(venue, field_name, new_value)

        return self.repository.save(venue)

    @staticmethod
    def _validate_operating_hours(
        opening_time: time,
        closing_time: time,
    ) -> None:
        """
        Valida el horario final de funcionamiento de una sede.

        La validacion utiliza tanto los valores actuales como los
        valores modificados para cubrir actualizaciones parciales.

        Raises:
            InvalidVenueHoursError: Cuando el cierre no es posterior
                a la apertura.
        """
        if closing_time <= opening_time:
            raise InvalidVenueHoursError(
                "El horario de cierre debe ser posterior al horario de apertura."
            )
