from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class PushDeviceRegister(BaseModel):
    """
    Representa los datos necesarios para registrar una instalacion.

    Flutter envia el identificador entregado por Firebase y la
    plataforma actual. El usuario se obtiene desde el token JWT.
    """

    installation_id: str = Field(
        min_length=1,
        max_length=255,
        examples=["firebase-installation-id"],
    )

    platform: Literal["android", "ios", "web"] = Field(
        examples=["android"],
    )

    @field_validator("installation_id")
    @classmethod
    def normalize_installation_id(
        cls,
        value: str,
    ) -> str:
        """
        Elimina espacios externos y rechaza identificadores vacios.
        """
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("El identificador de instalacion no puede estar vacio.")

        return normalized_value

    @field_validator("platform", mode="before")
    @classmethod
    def normalize_platform(
        cls,
        value: object,
    ) -> object:
        """
        Normaliza la plataforma antes de validar los valores permitidos.
        """
        if not isinstance(value, str):
            return value

        normalized_value = value.strip().lower()

        supported_platforms = {
            "android",
            "ios",
            "web",
        }

        if normalized_value not in supported_platforms:
            raise ValueError("Plataforma no soportada.")

        return normalized_value

    # Rechaza campos internos como user_id, id o is_active.
    model_config = ConfigDict(extra="forbid")


class PushDeviceResponse(BaseModel):
    """
    Representa la informacion publica de una instalacion registrada.
    """

    id: int
    user_id: int
    installation_id: str
    platform: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Permite construir la respuesta desde un modelo SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)
