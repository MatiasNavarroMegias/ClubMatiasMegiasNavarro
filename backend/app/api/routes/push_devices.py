from fastapi import APIRouter, status

from app.api.dependencies import (
    CurrentUser,
    PushDeviceServiceDependency,
)
from app.schemas import (
    PushDeviceRegister,
    PushDeviceResponse,
)

# Agrupa los endpoints de instalaciones para notificaciones push.
router = APIRouter(
    prefix="/push-devices",
    tags=["Push Devices"],
)


@router.post(
    "",
    response_model=PushDeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_push_device(
    registration_data: PushDeviceRegister,
    current_user: CurrentUser,
    service: PushDeviceServiceDependency,
) -> PushDeviceResponse:
    """
    Registra una instalacion para recibir notificaciones push.

    El usuario propietario se obtiene exclusivamente desde el token
    JWT. El cliente solamente informa el identificador entregado por
    Firebase y la plataforma actual.
    """
    push_device = service.register(
        user=current_user,
        installation_id=registration_data.installation_id,
        platform=registration_data.platform,
    )

    return PushDeviceResponse.model_validate(push_device)
