from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import SportsSpaceServiceDependency
from app.schemas import (
    SportsSpaceCreate,
    SportsSpaceResponse,
    SportsSpaceUpdate,
)
from app.services import (
    SportsSpaceAlreadyExistsError,
    SportsSpaceNoChangesError,
    SportsSpaceNotFoundError,
    SportsSpaceVenueInactiveError,
    SportsSpaceVenueNotFoundError,
)

# Agrupa los endpoints relacionados con espacios deportivos.
router = APIRouter(
    prefix="/sports-spaces",
    tags=["Sports Spaces"],
)


@router.get(
    "",
    response_model=list[SportsSpaceResponse],
    status_code=status.HTTP_200_OK,
)
def list_sports_spaces(
    service: SportsSpaceServiceDependency,
    venue_id: Annotated[
        int | None,
        Query(
            gt=0,
            description="Filtra los espacios por sede.",
        ),
    ] = None,
    sport_type: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=50,
            description="Filtra los espacios por tipo de deporte.",
        ),
    ] = None,
    is_active: Annotated[
        bool | None,
        Query(
            description=(
                "Filtra por estado. True devuelve activos, "
                "False devuelve inactivos y sin valor devuelve todos."
            ),
        ),
    ] = None,
) -> list[SportsSpaceResponse]:
    """
    Devuelve los espacios deportivos que cumplen los filtros.

    Los filtros por sede, deporte y estado pueden utilizarse de forma
    individual o combinada.

    El filtro is_active utiliza tres estados:

    - True: devuelve solamente espacios activos.
    - False: devuelve solamente espacios inactivos.
    - None: devuelve activos e inactivos.
    """
    try:
        sports_spaces = service.list_sports_spaces(
            venue_id=venue_id,
            sport_type=sport_type,
            is_active=is_active,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return [SportsSpaceResponse.model_validate(sports_space) for sports_space in sports_spaces]


@router.get(
    "/{sports_space_id}",
    response_model=SportsSpaceResponse,
    status_code=status.HTTP_200_OK,
)
def get_sports_space(
    sports_space_id: int,
    service: SportsSpaceServiceDependency,
) -> SportsSpaceResponse:
    """
    Devuelve un espacio deportivo mediante su identificador.

    Raises:
        HTTPException: Con codigo 404 cuando el espacio no existe.
    """
    try:
        sports_space = service.get_sports_space(
            sports_space_id,
        )
    except SportsSpaceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return SportsSpaceResponse.model_validate(
        sports_space,
    )


@router.post(
    "",
    response_model=SportsSpaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sports_space(
    sports_space_data: SportsSpaceCreate,
    service: SportsSpaceServiceDependency,
) -> SportsSpaceResponse:
    """
    Crea un espacio deportivo dentro de una sede activa.

    Raises:
        HTTPException: Con codigo 404 cuando la sede no existe.
        HTTPException: Con codigo 409 cuando la sede esta inactiva.
        HTTPException: Con codigo 409 cuando el espacio esta duplicado.
    """
    try:
        sports_space = service.create_sports_space(
            sports_space_data,
        )
    except SportsSpaceVenueNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except (
        SportsSpaceVenueInactiveError,
        SportsSpaceAlreadyExistsError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return SportsSpaceResponse.model_validate(
        sports_space,
    )


@router.patch(
    "/{sports_space_id}",
    response_model=SportsSpaceResponse,
    status_code=status.HTTP_200_OK,
)
def update_sports_space(
    sports_space_id: int,
    sports_space_data: SportsSpaceUpdate,
    service: SportsSpaceServiceDependency,
) -> SportsSpaceResponse:
    """
    Modifica parcialmente un espacio deportivo.

    La sede no puede modificarse. El servicio comprueba que la
    identidad final no colisione con otro espacio de la misma sede.

    Raises:
        HTTPException: Con codigo 404 cuando el espacio no existe.
        HTTPException: Con codigo 400 cuando no existen cambios.
        HTTPException: Con codigo 409 cuando la identidad esta duplicada.
    """
    try:
        sports_space = service.update_sports_space(
            sports_space_id=sports_space_id,
            sports_space_data=sports_space_data,
        )
    except SportsSpaceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except SportsSpaceNoChangesError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SportsSpaceAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return SportsSpaceResponse.model_validate(
        sports_space,
    )
