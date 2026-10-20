from datetime import datetime, time
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VenueBase(BaseModel):
    """
    Contiene los campos compartidos por los esquemas de sede.

    Esta clase evita repetir las mismas reglas de nombre, direccion
    y horarios dentro de los demas esquemas.
    """

    # Nombre visible de la sede.
    #
    # Las longitudes coinciden con la columna definida en el
    # modelo SQLAlchemy para evitar inconsistencias.
    name: str = Field(
        min_length=1,
        max_length=100,
        examples=["Sede Ramos Mejia"],
    )

    # Direccion fisica de la sede.
    address: str = Field(
        min_length=1,
        max_length=200,
        examples=["Avenida de Mayo 1000"],
    )

    # Horario habitual de apertura.
    opening_time: time

    # Horario habitual de cierre.
    closing_time: time

    @model_validator(mode="after")
    def validate_operating_hours(self) -> Self:
        """
        Verifica que el cierre sea posterior a la apertura.

        Esta regla impide registrar un rango horario vacio
        o con los horarios invertidos.
        """
        if self.closing_time <= self.opening_time:
            raise ValueError("El horario de cierre debe ser posterior al horario de apertura.")

        return self


class VenueCreate(VenueBase):
    """
    Representa los datos necesarios para crear una sede.

    El cliente no envia el identificador, el estado ni las fechas
    porque esos valores son administrados por el backend.
    """


class VenueUpdate(BaseModel):
    """
    Representa los datos permitidos durante la edicion de una sede.

    Todos los campos son opcionales porque una solicitud PATCH
    envia solamente los valores que fueron modificados.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    address: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    opening_time: time | None = None
    closing_time: time | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_complete_operating_hours(self) -> Self:
        """
        Valida los horarios cuando ambos se reciben juntos.

        Si la solicitud modifica solamente uno de los horarios,
        el servicio debera combinar el cambio con el valor actual
        almacenado en PostgreSQL antes de realizar la validacion final.
        """
        both_hours_were_sent = self.opening_time is not None and self.closing_time is not None

        if both_hours_were_sent and self.closing_time <= self.opening_time:
            raise ValueError("El horario de cierre debe ser posterior al horario de apertura.")

        return self


class VenueResponse(VenueBase):
    """
    Representa la informacion de una sede devuelta por la API.

    Incluye los valores administrados por PostgreSQL, como el
    identificador, el estado y las fechas de auditoria.
    """

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Permite crear el esquema desde una instancia de Venue.
    model_config = ConfigDict(from_attributes=True)
