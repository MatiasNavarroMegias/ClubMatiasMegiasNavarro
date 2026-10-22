from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthServiceDependency
from app.schemas import UserRegister, UserResponse
from app.services import EmailAlreadyRegisteredError

# Agrupa los endpoints relacionados con autenticacion.
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    registration_data: UserRegister,
    service: AuthServiceDependency,
) -> UserResponse:
    """
    Registra un usuario utilizando datos previamente validados.

    El esquema valida y normaliza los datos. El servicio comprueba
    si el correo ya existe, genera un hash Argon2 y persiste la cuenta.

    Raises:
        HTTPException: Con codigo 409 cuando el correo ya pertenece
            a otra cuenta.
    """
    try:
        user = service.register_user(registration_data)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return UserResponse.model_validate(user)
