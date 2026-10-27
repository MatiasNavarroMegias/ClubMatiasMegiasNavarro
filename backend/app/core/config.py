from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Representa la configuracion general del backend.

    Los valores se obtienen desde variables de entorno o desde el
    archivo .env utilizado durante el desarrollo local.

    Pydantic valida y convierte automaticamente los valores recibidos.
    Por ejemplo, el texto "true" se convierte en el booleano True.
    """

    # Nombre utilizado para identificar la API.
    app_name: str = "ClubMatiasMegiasNavarro API"

    # Entorno donde se encuentra ejecutando la aplicacion.
    # Literal limita los valores posibles y evita errores de escritura.
    app_env: Literal["development", "testing", "production"] = "development"

    # Indica si las herramientas de depuracion deben estar activas.
    app_debug: bool = False

    # Zona horaria utilizada para interpretar horarios de sedes,
    # disponibilidad y reservas.
    #
    # Se utiliza un nombre de la base IANA para contemplar correctamente
    # las reglas horarias del lugar donde funciona la aplicacion.
    app_timezone: str = "America/Argentina/Buenos_Aires"

    # Direccion utilizada por SQLAlchemy para conectarse con PostgreSQL.
    database_url: str

    # Clave secreta utilizada para firmar y verificar tokens JWT.
    #
    # No posee un valor predeterminado porque debe definirse de forma
    # segura en cada entorno y nunca almacenarse dentro del repositorio.
    jwt_secret_key: str = Field(
        min_length=32,
    )

    # Algoritmo simetrico utilizado para firmar los tokens.
    #
    # Por ahora se restringe a HS256 para evitar configuraciones
    # accidentales con algoritmos no contemplados por la aplicacion.
    jwt_algorithm: Literal["HS256"] = "HS256"

    # Duracion del token de acceso expresada en minutos.
    #
    # El valor debe ser positivo y puede modificarse mediante una
    # variable de entorno sin cambiar el codigo.
    access_token_expire_minutes: int = Field(
        default=60,
        gt=0,
    )

    @field_validator("app_timezone")
    @classmethod
    def validate_app_timezone(
        cls,
        value: str,
    ) -> str:
        """
        Verifica que la zona horaria exista dentro de la base IANA.

        Args:
            value: Nombre configurado para la zona horaria.

        Returns:
            Nombre validado de la zona horaria.

        Raises:
            ValueError: Cuando la zona horaria no existe.
        """
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("La zona horaria de la aplicacion no puede estar vacia.")

        try:
            ZoneInfo(normalized_value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("La zona horaria de la aplicacion no es valida.") from error

        return normalized_value

    # Configura la lectura del archivo .env.
    #
    # extra="ignore" evita errores si el archivo contiene variables
    # que todavia no forman parte de esta clase.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Devuelve una unica instancia reutilizable de la configuracion.

    lru_cache evita leer y validar el archivo .env cada vez que una
    parte de la aplicacion necesita acceder a la configuracion.

    Returns:
        La configuracion validada del backend.
    """
    return Settings()
