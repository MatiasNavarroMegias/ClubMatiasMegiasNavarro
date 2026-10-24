from app.models import SportsSpace
from app.repositories import SportsSpaceRepository, VenueRepository
from app.schemas import SportsSpaceCreate, SportsSpaceUpdate


class SportsSpaceNotFoundError(Exception):
    """
    Indica que el espacio deportivo solicitado no existe.

    El servicio utiliza una excepcion propia para no depender de
    FastAPI ni de codigos HTTP.
    """


class SportsSpaceAlreadyExistsError(Exception):
    """
    Indica que ya existe un espacio con la misma identidad.

    La identidad de un espacio se compone por la sede, el tipo de
    deporte y el numero asignado dentro de esa sede.
    """


class SportsSpaceNoChangesError(Exception):
    """
    Indica que la solicitud no contiene modificaciones efectivas.

    Esta excepcion evita confirmar transacciones que no producen
    cambios reales sobre el espacio deportivo.
    """


class SportsSpaceVenueNotFoundError(Exception):
    """
    Indica que la sede recibida durante la creacion no existe.
    """


class SportsSpaceVenueInactiveError(Exception):
    """
    Indica que no puede crearse un espacio dentro de una sede inactiva.
    """


class SportsSpaceService:
    """
    Aplica las reglas de negocio de los espacios deportivos.

    El servicio valida las sedes, evita espacios duplicados y coordina
    las operaciones de consulta y persistencia de los repositorios.
    """

    def __init__(
        self,
        repository: SportsSpaceRepository,
        venue_repository: VenueRepository,
    ) -> None:
        """
        Inicializa el servicio con los repositorios necesarios.

        Args:
            repository: Repositorio de espacios deportivos.
            venue_repository: Repositorio utilizado para validar sedes.
        """
        self.repository = repository
        self.venue_repository = venue_repository

    def list_sports_spaces(
        self,
        *,
        venue_id: int | None = None,
        sport_type: str | None = None,
        active_only: bool = False,
    ) -> list[SportsSpace]:
        """
        Lista los espacios que cumplen los filtros recibidos.

        El tipo deportivo se normaliza antes de enviarlo al repositorio
        para mantener consultas consistentes.

        Los filtros pueden utilizarse individualmente o combinarse.

        Args:
            venue_id: Identificador opcional de la sede.
            sport_type: Tipo deportivo opcional.
            active_only: Indica si deben excluirse espacios inactivos.

        Returns:
            Lista de espacios ordenada por el repositorio.

        Raises:
            ValueError: Cuando sport_type contiene solamente espacios.
        """
        normalized_sport_type = self._normalize_optional_sport_type(
            sport_type,
        )

        return self.repository.list_all(
            venue_id=venue_id,
            sport_type=normalized_sport_type,
            active_only=active_only,
        )

    def get_sports_space(
        self,
        sports_space_id: int,
    ) -> SportsSpace:
        """
        Obtiene un espacio deportivo mediante su identificador.

        Args:
            sports_space_id: Identificador interno del espacio.

        Returns:
            Espacio deportivo encontrado.

        Raises:
            SportsSpaceNotFoundError: Cuando el espacio no existe.
        """
        sports_space = self.repository.get_by_id(
            sports_space_id,
        )

        if sports_space is None:
            raise SportsSpaceNotFoundError(
                f"No existe un espacio deportivo con el identificador {sports_space_id}."
            )

        return sports_space

    def create_sports_space(
        self,
        sports_space_data: SportsSpaceCreate,
    ) -> SportsSpace:
        """
        Crea un espacio deportivo dentro de una sede activa.

        Antes de construir el modelo, el servicio verifica que la sede
        exista, permanezca activa y no tenga otro espacio con el mismo
        deporte y numero.

        Args:
            sports_space_data: Datos validados del nuevo espacio.

        Returns:
            Espacio persistido con los valores generados por PostgreSQL.

        Raises:
            SportsSpaceVenueNotFoundError: Cuando la sede no existe.
            SportsSpaceVenueInactiveError: Cuando la sede esta inactiva.
            SportsSpaceAlreadyExistsError: Cuando ya existe la misma
                combinacion de sede, deporte y numero.
        """
        venue = self.venue_repository.get_by_id(
            sports_space_data.venue_id,
        )

        if venue is None:
            raise SportsSpaceVenueNotFoundError(
                f"No existe una sede con el identificador {sports_space_data.venue_id}."
            )

        if not venue.is_active:
            raise SportsSpaceVenueInactiveError(
                "No se pueden agregar espacios deportivos a una sede inactiva."
            )

        existing_space = self.repository.get_by_identity(
            venue_id=sports_space_data.venue_id,
            sport_type=sports_space_data.sport_type,
            space_number=sports_space_data.space_number,
        )

        if existing_space is not None:
            raise SportsSpaceAlreadyExistsError(
                "Ya existe un espacio deportivo con ese deporte y numero dentro de la sede."
            )

        sports_space = SportsSpace(
            venue_id=sports_space_data.venue_id,
            name=sports_space_data.name,
            sport_type=sports_space_data.sport_type,
            space_number=sports_space_data.space_number,
            is_active=True,
        )

        return self.repository.add(sports_space)

    def update_sports_space(
        self,
        sports_space_id: int,
        sports_space_data: SportsSpaceUpdate,
    ) -> SportsSpace:
        """
        Modifica parcialmente un espacio deportivo existente.

        La sede no puede modificarse. Si cambia el deporte o el numero,
        se comprueba que la identidad final no pertenezca a otro
        espacio dentro de la misma sede.

        Args:
            sports_space_id: Identificador del espacio.
            sports_space_data: Campos recibidos mediante PATCH.

        Returns:
            Espacio deportivo actualizado.

        Raises:
            SportsSpaceNotFoundError: Cuando el espacio no existe.
            SportsSpaceNoChangesError: Cuando no se recibieron campos
                o los valores coinciden con los datos actuales.
            SportsSpaceAlreadyExistsError: Cuando la identidad final
                pertenece a otro espacio.
        """
        sports_space = self.get_sports_space(
            sports_space_id,
        )

        changes = sports_space_data.model_dump(
            exclude_unset=True,
        )

        if not changes:
            raise SportsSpaceNoChangesError("La solicitud no contiene campos para modificar.")

        effective_changes = {
            field_name: new_value
            for field_name, new_value in changes.items()
            if getattr(sports_space, field_name) != new_value
        }

        if not effective_changes:
            raise SportsSpaceNoChangesError(
                "Los valores recibidos coinciden con los datos actuales."
            )

        final_sport_type = effective_changes.get(
            "sport_type",
            sports_space.sport_type,
        )
        final_space_number = effective_changes.get(
            "space_number",
            sports_space.space_number,
        )

        identity_was_modified = (
            final_sport_type != sports_space.sport_type
            or final_space_number != sports_space.space_number
        )

        if identity_was_modified:
            self._ensure_identity_is_available(
                sports_space=sports_space,
                sport_type=final_sport_type,
                space_number=final_space_number,
            )

        for field_name, new_value in effective_changes.items():
            setattr(
                sports_space,
                field_name,
                new_value,
            )

        return self.repository.save(sports_space)

    def _ensure_identity_is_available(
        self,
        *,
        sports_space: SportsSpace,
        sport_type: str,
        space_number: int,
    ) -> None:
        """
        Verifica que la identidad final no pertenezca a otro espacio.

        El repositorio puede devolver el mismo espacio que se esta
        actualizando. Ese resultado no representa una colision.

        Args:
            sports_space: Espacio que se esta modificando.
            sport_type: Tipo deportivo final.
            space_number: Numero final dentro de la sede.

        Raises:
            SportsSpaceAlreadyExistsError: Cuando la identidad final
                pertenece a otro registro.
        """
        existing_space = self.repository.get_by_identity(
            venue_id=sports_space.venue_id,
            sport_type=sport_type,
            space_number=space_number,
        )

        if existing_space is not None and existing_space.id != sports_space.id:
            raise SportsSpaceAlreadyExistsError(
                "Ya existe un espacio deportivo con ese deporte y numero dentro de la sede."
            )

    @staticmethod
    def _normalize_optional_sport_type(
        sport_type: str | None,
    ) -> str | None:
        """
        Normaliza un filtro deportivo opcional.

        Args:
            sport_type: Valor recibido desde el filtro de consulta.

        Returns:
            Tipo deportivo normalizado o None cuando no se recibio.

        Raises:
            ValueError: Cuando el filtro contiene solamente espacios.
        """
        if sport_type is None:
            return None

        normalized_sport_type = sport_type.strip()

        if not normalized_sport_type:
            raise ValueError("El tipo de deporte no puede contener solo espacios.")

        return normalized_sport_type.title()
