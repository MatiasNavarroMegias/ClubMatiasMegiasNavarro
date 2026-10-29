from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class PasswordRecoveryRequest(BaseModel):
    """
    Representa la solicitud inicial de recuperacion.

    El correo se normaliza antes de consultar PostgreSQL.
    """

    email: EmailStr = Field(
        examples=["matias@example.com"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value,
    ):
        """
        Normaliza el correo recibido.
        """
        return str(value).strip().lower()

    model_config = ConfigDict(
        extra="forbid",
    )


class PasswordRecoveryConfirm(BaseModel):
    """
    Representa la confirmacion de recuperacion.

    Requiere el correo, el codigo temporal, la nueva contrasena y su
    confirmacion.
    """

    email: EmailStr = Field(
        examples=["matias@example.com"],
    )

    code: str = Field(
        min_length=8,
        max_length=8,
        pattern=r"^\d{8}$",
        examples=["48392175"],
    )

    new_password: str = Field(
        min_length=8,
        max_length=128,
        examples=["NuevaClave123"],
    )

    new_password_confirmation: str = Field(
        min_length=8,
        max_length=128,
        examples=["NuevaClave123"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value,
    ):
        """
        Normaliza el correo antes de buscar la cuenta.
        """
        return str(value).strip().lower()

    @field_validator(
        "new_password",
        "new_password_confirmation",
    )
    @classmethod
    def validate_password_security(
        cls,
        value,
    ):
        """
        Aplica la misma politica utilizada durante el registro.
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
    def validate_password_confirmation(self):
        """
        Verifica que ambas contrasenas coincidan.
        """
        if self.new_password != self.new_password_confirmation:
            raise ValueError("Las contrasenas ingresadas no coinciden.")

        return self

    model_config = ConfigDict(
        extra="forbid",
    )


class PasswordRecoveryMessage(BaseModel):
    """
    Representa una respuesta informativa del flujo.
    """

    message: str
