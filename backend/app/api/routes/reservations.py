from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import (
    CurrentUser,
    ReservationServiceDependency,
)
from app.schemas import ReservationCreate, ReservationResponse
from app.services import (
    ReservationInvalidStartTimeError,
    ReservationOutsideVenueHoursError,
    ReservationSportsSpaceInactiveError,
    ReservationSportsSpaceNotFoundError,
    ReservationStartInPastError,
    ReservationTimeConflictError,
    ReservationVenueInactiveError,
)

# Agrupa los endpoints relacionados con reservas.
router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"],
)


@router.post(
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation(
    reservation_data: ReservationCreate,
    current_user: CurrentUser,
    service: ReservationServiceDependency,
) -> ReservationResponse:
    """
    Crea una reserva confirmada para el usuario autenticado.

    El usuario se obtiene desde el token Bearer. El cliente solamente
    envia el espacio deportivo y el horario de inicio. El servicio
    calcula la finalizacion, valida el horario y evita superposiciones.

    Raises:
        HTTPException: Con codigo 404 cuando el espacio no existe.
        HTTPException: Con codigo 409 cuando el espacio o la sede se
            encuentran inactivos.
        HTTPException: Con codigo 409 cuando el turno ya esta reservado.
        HTTPException: Con codigo 422 cuando el horario es pasado, no
            comienza en una hora completa o queda fuera del horario
            de funcionamiento de la sede.
    """
    try:
        reservation = service.create_reservation(
            user_id=current_user.id,
            reservation_data=reservation_data,
        )
    except ReservationSportsSpaceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except (
        ReservationSportsSpaceInactiveError,
        ReservationVenueInactiveError,
        ReservationTimeConflictError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except (
        ReservationStartInPastError,
        ReservationInvalidStartTimeError,
        ReservationOutsideVenueHoursError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return ReservationResponse.model_validate(
        reservation,
    )
