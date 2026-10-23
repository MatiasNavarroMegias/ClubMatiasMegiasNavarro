from datetime import date, datetime
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class UserRegister(BaseModel):
    """
    Representa los datos necesarios para registrar un usuario.

    El esquema valida el perfil, normaliza el correo y comprueba
    requisitos minimos de seguridad para la contrasena.
    """

    first_name: str = Field(
        min_length=1,
        max_length=50,
        examples=["Matias"],
    )

    last_name: str = Field(
        min_length=1,
        max_length=50,
        examples=["Megias Navarro"],
    )

    birth_date: date = Field(
        examples=["2000-01-15"],
    )

    email: EmailStr = Field(
        examples=["matias@example.com"],
    )

    password: str = Field(
        min_length=8,
        max_length=128,
        examples=["ClaveSegura123"],
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_person_name(cls, value: str) -> str:
        """
        Elimina espacios externos y rechaza texto compuesto solo por espacios.
        """
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("El nombre y el apellido no pueden contener solo espacios.")

        return normalized_value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """
        Normaliza el correo para evitar diferencias por mayusculas.

        La normalizacion permite tratar MATIAS@EXAMPLE.COM y
        matias@example.com como la misma cuenta.
        """
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_security(cls, value: str) -> str:
        """
        Comprueba los requisitos minimos de seguridad de la contrasena.
        """
        if value != value.strip():
            raise ValueError("La contrasena no puede comenzar ni terminar con espacios.")

        if not any(character.isupper() for character in value):
            raise ValueError("La contrasena debe incluir al menos una letra mayuscula.")

        if not any(character.islower() for character in value):
            raise ValueError("La contrasena debe incluir al menos una letra minuscula.")

        if not any(character.isdigit() for character in value):
            raise ValueError("La contrasena debe incluir al menos un numero.")

        return value

    @model_validator(mode="after")
    def validate_birth_date(self) -> Self:
        """
        Verifica que la fecha de nacimiento sea anterior al dia actual.
        """
        if self.birth_date >= date.today():
            raise ValueError("La fecha de nacimiento debe ser anterior al dia actual.")

        return self


class UserLogin(BaseModel):
    """
    Representa las credenciales necesarias para iniciar sesion.

    El correo se valida y normaliza antes de consultar PostgreSQL.
    La contrasena no se modifica porque debe verificarse exactamente
    como fue ingresada por el usuario.
    """

    email: EmailStr = Field(
        examples=["matias@example.com"],
    )

    password: str = Field(
        min_length=1,
        max_length=128,
        examples=["ClaveSegura123"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """
        Normaliza el correo antes de buscar la cuenta.
        """
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_whitespace(cls, value: str) -> str:
        """
        Rechaza espacios externos sin alterar la contrasena recibida.
        """
        if value != value.strip():
            raise ValueError("La contrasena no puede comenzar ni terminar con espacios.")

        return value


class UserUpdate(BaseModel):
    """
    Representa los campos editables del perfil.

    Todos los campos son opcionales para permitir actualizaciones
    parciales. El correo no forma parte del esquema porque no puede
    modificarse desde el perfil.
    """

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        examples=["Matias"],
    )

    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        examples=["Megias Navarro"],
    )

    birth_date: date | None = Field(
        default=None,
        examples=["2000-01-15"],
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_optional_person_name(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normaliza los nombres recibidos en una actualizacion parcial.
        """
        if value is None:
            return None

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("El nombre y el apellido no pueden contener solo espacios.")

        return normalized_value

    @field_validator("birth_date")
    @classmethod
    def validate_optional_birth_date(
        cls,
        value: date | None,
    ) -> date | None:
        """
        Verifica que la fecha de nacimiento sea anterior al dia actual.
        """
        if value is not None and value >= date.today():
            raise ValueError("La fecha de nacimiento debe ser anterior al dia actual.")

        return value

        # Rechaza campos que no pertenecen al perfil editable.

    #
    # Esto impide intentar modificar email, password_hash, is_active,
    # id u otros campos no contemplados por este esquema.
    model_config = ConfigDict(extra="forbid")


class TokenResponse(BaseModel):
    """
    Representa el token entregado despues de un login exitoso.

    El tipo bearer indica que Flutter debe enviar el token mediante
    el encabezado Authorization.
    """

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """
    Representa la informacion publica de un usuario.

    La respuesta no incluye la contrasena recibida ni password_hash.
    """

    id: int
    first_name: str
    last_name: str
    birth_date: date
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Permite construir la respuesta desde una instancia SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)
