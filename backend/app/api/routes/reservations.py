from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import (
    CurrentUser,
    ReservationServiceDependency,
)
from app.schemas import ReservationCreate, ReservationResponse
from app.services import (
    ReservationAlreadyCancelledError,
    ReservationAlreadyStartedError,
    ReservationInvalidStartTimeError,
    ReservationNotFoundError,
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


@router.get(
    "/upcoming",
    response_model=list[ReservationResponse],
    status_code=status.HTTP_200_OK,
)
def list_upcoming_reservations(
    current_user: CurrentUser,
    service: ReservationServiceDependency,
) -> list[ReservationResponse]:
    """
    Devuelve las proximas reservas del usuario autenticado.

    Solamente se incluyen reservas confirmadas cuyo horario de inicio
    sea igual o posterior al momento actual.
    """
    reservations = service.list_upcoming_reservations(
        user_id=current_user.id,
    )

    return [ReservationResponse.model_validate(reservation) for reservation in reservations]


@router.get(
    "/history",
    response_model=list[ReservationResponse],
    status_code=status.HTTP_200_OK,
)
def list_reservation_history(
    current_user: CurrentUser,
    service: ReservationServiceDependency,
) -> list[ReservationResponse]:
    """
    Devuelve el historial del usuario autenticado.

    El historial incluye reservas canceladas y reservas confirmadas
    cuyo horario ya finalizo.
    """
    reservations = service.list_reservation_history(
        user_id=current_user.id,
    )

    return [ReservationResponse.model_validate(reservation) for reservation in reservations]


@router.patch(
    "/{reservation_id}/cancel",
    response_model=ReservationResponse,
    status_code=status.HTTP_200_OK,
)
def cancel_reservation(
    reservation_id: int,
    current_user: CurrentUser,
    service: ReservationServiceDependency,
) -> ReservationResponse:
    """
    Cancela una reserva futura del usuario autenticado.

    La reserva se conserva para el historial. Su estado cambia a
    cancelled y se registra el momento de la cancelacion.

    Raises:
        HTTPException: Con codigo 404 cuando la reserva no existe o no
            pertenece al usuario autenticado.
        HTTPException: Con codigo 409 cuando la reserva ya esta
            cancelada o ya comenzo.
    """
    try:
        reservation = service.cancel_reservation(
            reservation_id=reservation_id,
            user_id=current_user.id,
        )
    except ReservationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except (
        ReservationAlreadyCancelledError,
        ReservationAlreadyStartedError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return ReservationResponse.model_validate(
        reservation,
    )
