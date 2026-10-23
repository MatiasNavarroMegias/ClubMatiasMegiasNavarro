from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthServiceDependency, CurrentUser
from app.schemas import UserResponse, UserUpdate

# Agrupa los endpoints personales del usuario autenticado.
router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_my_profile(
    current_user: CurrentUser,
) -> UserResponse:
    """
    Devuelve el perfil del usuario autenticado.

    La identidad se obtiene exclusivamente desde el token JWT. El
    cliente no puede indicar manualmente otro identificador de usuario.
    """
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def update_my_profile(
    update_data: UserUpdate,
    current_user: CurrentUser,
    service: AuthServiceDependency,
) -> UserResponse:
    """
    Actualiza los campos editables del perfil autenticado.

    El correo no forma parte de UserUpdate y, por lo tanto, no puede
    modificarse mediante este endpoint.
    """
    try:
        updated_user = service.update_profile(
            user=current_user,
            update_data=update_data,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return UserResponse.model_validate(updated_user)
