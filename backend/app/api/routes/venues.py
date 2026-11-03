from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import VenueServiceDependency
from app.schemas import VenueCreate, VenueResponse, VenueUpdate
from app.services import (
    InvalidVenueHoursError,
    VenueNoChangesError,
    VenueNotFoundError,
)

# Agrupa todos los endpoints relacionados con sedes.
router = APIRouter(
    prefix="/venues",
    tags=["Venues"],
)


@router.get(
    "",
    response_model=list[VenueResponse],
    status_code=status.HTTP_200_OK,
)
def list_venues(
    service: VenueServiceDependency,
) -> list[VenueResponse]:
    """
    Devuelve todas las sedes ordenadas por nombre.

    El repositorio construye la consulta y el servicio coordina
    la operacion. FastAPI convierte los modelos SQLAlchemy en
    esquemas VenueResponse.
    """
    venues = service.list_venues()

    return [VenueResponse.model_validate(venue) for venue in venues]


@router.get(
    "/{venue_id}",
    response_model=VenueResponse,
    status_code=status.HTTP_200_OK,
)
def get_venue(
    venue_id: int,
    service: VenueServiceDependency,
) -> VenueResponse:
    """
    Devuelve una sede mediante su identificador.

    Raises:
        HTTPException: Con codigo 404 cuando la sede no existe.
    """
    try:
        venue = service.get_venue(venue_id)
    except VenueNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return VenueResponse.model_validate(venue)


@router.post(
    "",
    response_model=VenueResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_venue(
    venue_data: VenueCreate,
    service: VenueServiceDependency,
) -> VenueResponse:
    """
    Crea una sede utilizando datos previamente validados.

    VenueCreate rechaza nombres, direcciones u horarios invalidos
    antes de ejecutar las reglas de negocio y la persistencia.
    """
    venue = service.create_venue(venue_data)

    return VenueResponse.model_validate(venue)


@router.patch(
    "/{venue_id}",
    response_model=VenueResponse,
    status_code=status.HTTP_200_OK,
)
def update_venue(
    venue_id: int,
    venue_data: VenueUpdate,
    service: VenueServiceDependency,
) -> VenueResponse:
    """
    Modifica parcialmente una sede existente.

    El endpoint traduce las excepciones del dominio a respuestas HTTP,
    pero no implementa directamente las reglas de negocio.
    """
    try:
        venue = service.update_venue(
            venue_id=venue_id,
            venue_data=venue_data,
        )
    except VenueNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except VenueNoChangesError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except InvalidVenueHoursError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return VenueResponse.model_validate(venue)
