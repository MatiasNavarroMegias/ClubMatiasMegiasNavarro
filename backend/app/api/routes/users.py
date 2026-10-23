from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser
from app.schemas import UserResponse

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
