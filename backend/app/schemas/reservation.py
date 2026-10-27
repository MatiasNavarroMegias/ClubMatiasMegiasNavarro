from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class ReservationCreate(BaseModel):
    """
    Representa los datos enviados para crear una reserva.

    El usuario se obtiene desde el token autenticado. La hora final,
    el estado y las fechas de auditoria son administrados por el
    backend y no deben ser enviados por el cliente.
    """

    sports_space_id: int = Field(
        gt=0,
        examples=[8],
    )

    start_at: datetime = Field(
        examples=["2026-11-02T18:00:00-03:00"],
    )

    @field_validator("start_at")
    @classmethod
    def validate_timezone(
        cls,
        value: datetime,
    ) -> datetime:
        """
        Verifica que la fecha incluya informacion de zona horaria.

        Una fecha sin zona horaria es ambigua y podria interpretarse
        de manera diferente entre Flutter, FastAPI y PostgreSQL.

        La fecha futura, la hora completa y la duracion se validaran
        posteriormente dentro del servicio.
        """
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("La fecha de inicio debe incluir una zona horaria.")

        return value

    # Impide que el cliente envie user_id, end_at, status y otros
    # campos administrados internamente.
    model_config = ConfigDict(
        extra="forbid",
    )


class ReservationResponse(BaseModel):
    """
    Representa una reserva devuelta por la API.

    Incluye los datos administrados por PostgreSQL y el estado actual
    de la reserva.
    """

    id: int
    user_id: int
    sports_space_id: int
    start_at: datetime
    end_at: datetime
    status: str
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Permite construir la respuesta desde una instancia SQLAlchemy.
    model_config = ConfigDict(
        from_attributes=True,
    )
