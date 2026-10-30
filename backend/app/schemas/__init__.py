"""Esquemas utilizados para validar entradas y construir respuestas."""

from app.schemas.password_recovery import (
    PasswordRecoveryConfirm,
    PasswordRecoveryMessage,
    PasswordRecoveryRequest,
)
from app.schemas.push_device import (
    PushDeviceRegister,
    PushDeviceResponse,
)
from app.schemas.reservation import (
    AvailabilitySlotResponse,
    ReservationCreate,
    ReservationResponse,
)
from app.schemas.sports_space import (
    SportsSpaceCreate,
    SportsSpaceResponse,
    SportsSpaceUpdate,
)
from app.schemas.user import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.schemas.venue import (
    VenueCreate,
    VenueResponse,
    VenueUpdate,
)

__all__ = [
    "AvailabilitySlotResponse",
    "PasswordRecoveryConfirm",
    "PasswordRecoveryMessage",
    "PasswordRecoveryRequest",
    "PushDeviceRegister",
    "PushDeviceResponse",
    "ReservationCreate",
    "ReservationResponse",
    "SportsSpaceCreate",
    "SportsSpaceResponse",
    "SportsSpaceUpdate",
    "TokenResponse",
    "UserLogin",
    "UserRegister",
    "UserResponse",
    "UserUpdate",
    "VenueCreate",
    "VenueResponse",
    "VenueUpdate",
]
