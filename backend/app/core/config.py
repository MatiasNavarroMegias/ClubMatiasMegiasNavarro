from functools import lru_cache
from typing import Literal

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

    # Direccion utilizada posteriormente por SQLAlchemy para conectarse
    # con PostgreSQL.
    database_url: str

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
