from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class SportsSpaceCreate(BaseModel):
    """
    Representa los datos necesarios para crear un espacio deportivo.

    El identificador, el estado y las fechas son administrados por
    PostgreSQL y no deben ser enviados por el cliente.
    """

    venue_id: int = Field(
        gt=0,
        examples=[1],
    )

    name: str = Field(
        min_length=1,
        max_length=100,
        examples=["Cancha de Futbol 1"],
    )

    sport_type: str = Field(
        min_length=1,
        max_length=50,
        examples=["Futbol"],
    )

    space_number: int = Field(
        gt=0,
        examples=[1],
    )

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """
        Elimina espacios externos del nombre visible.

        La validacion impide que un texto compuesto solamente por
        espacios sea aceptado como nombre.
        """
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("El nombre del espacio no puede contener solo espacios.")

        return normalized_value

    @field_validator("sport_type")
    @classmethod
    def normalize_sport_type(cls, value: str) -> str:
        """
        Normaliza el tipo deportivo para mantener valores consistentes.

        title convierte, por ejemplo, futbol y FUTBOL en Futbol.
        """
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("El tipo de deporte no puede contener solo espacios.")

        return normalized_value.title()

    # Rechaza identificadores, estados o fechas enviados manualmente.
    model_config = ConfigDict(extra="forbid")


class SportsSpaceUpdate(BaseModel):
    """
    Representa una actualizacion parcial de un espacio deportivo.

    La sede no puede modificarse para evitar trasladar un espacio que
    pueda tener reservas o informacion historica asociada.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    sport_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    space_number: int | None = Field(
        default=None,
        gt=0,
    )

    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_optional_name(
        cls,
        value: str | None,
    ) -> str:
        """
        Normaliza el nombre cuando se incluye en la solicitud.

        El campo puede omitirse, pero no puede enviarse como null.
        """
        if value is None:
            raise ValueError("El nombre del espacio no puede ser nulo.")

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("El nombre del espacio no puede contener solo espacios.")

        return normalized_value

    @field_validator("sport_type")
    @classmethod
    def normalize_optional_sport_type(
        cls,
        value: str | None,
    ) -> str:
        """
        Normaliza el deporte cuando se incluye en la solicitud.

        El campo puede omitirse, pero no puede enviarse como null.
        """
        if value is None:
            raise ValueError("El tipo de deporte no puede ser nulo.")

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("El tipo de deporte no puede contener solo espacios.")

        return normalized_value.title()

    # Impide modificar venue_id, id y campos de auditoria.
    model_config = ConfigDict(extra="forbid")


class SportsSpaceResponse(BaseModel):
    """
    Representa un espacio deportivo devuelto por la API.

    La disponibilidad no se incluye porque se calculara posteriormente
    para una fecha y un rango horario determinados.
    """

    id: int
    venue_id: int
    name: str
    sport_type: str
    space_number: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Permite construir la respuesta desde el modelo SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)
