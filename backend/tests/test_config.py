import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings

TEST_DATABASE_URL = "postgresql+psycopg://test:test@localhost:5432/test_database"
TEST_JWT_SECRET_KEY = "test-secret-key-with-at-least-32-characters"


def configure_required_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Configura las variables obligatorias para una prueba.

    Los valores son ficticios y existen solamente durante la ejecucion
    de la prueba. No contienen credenciales reales.
    """
    monkeypatch.setenv(
        "DATABASE_URL",
        TEST_DATABASE_URL,
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        TEST_JWT_SECRET_KEY,
    )


def test_settings_read_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que la configuracion lea y convierta variables de entorno.

    monkeypatch permite definir variables temporales solamente durante
    esta prueba. De esta forma, la prueba no depende del archivo .env
    ni utiliza credenciales reales.
    """
    configure_required_environment(monkeypatch)

    monkeypatch.setenv("APP_NAME", "API de prueba")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "90")

    settings = Settings(_env_file=None)

    assert settings.app_name == "API de prueba"
    assert settings.app_env == "testing"
    assert settings.app_debug is True
    assert settings.database_url.endswith("/test_database")
    assert settings.jwt_secret_key == TEST_JWT_SECRET_KEY
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 90


def test_settings_use_token_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica los valores predeterminados no sensibles del token.
    """
    configure_required_environment(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 60


def test_settings_reject_missing_jwt_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que la aplicacion no inicie sin una clave JWT.
    """
    monkeypatch.setenv(
        "DATABASE_URL",
        TEST_DATABASE_URL,
    )
    monkeypatch.delenv(
        "JWT_SECRET_KEY",
        raising=False,
    )

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_reject_short_jwt_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que una clave JWT demasiado corta sea rechazada.
    """
    monkeypatch.setenv(
        "DATABASE_URL",
        TEST_DATABASE_URL,
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "short-key",
    )

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_reject_invalid_token_expiration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que la duracion del token sea mayor que cero.
    """
    configure_required_environment(monkeypatch)
    monkeypatch.setenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "0",
    )

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_reject_invalid_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que un entorno desconocido produzca un error de validacion.

    La propiedad app_env acepta solamente development, testing o
    production. Esta restriccion evita iniciar la API con una
    configuracion escrita incorrectamente.
    """
    configure_required_environment(monkeypatch)
    monkeypatch.setenv("APP_ENV", "invalid")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_get_settings_reuses_cached_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que get_settings reutilice la misma instancia.

    La cache evita leer y validar la configuracion varias veces durante
    una misma ejecucion del backend.
    """
    configure_required_environment(monkeypatch)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("APP_DEBUG", "false")

    # Limpia cualquier instancia creada por pruebas o ejecuciones anteriores.
    get_settings.cache_clear()

    first_settings = get_settings()
    second_settings = get_settings()

    assert first_settings is second_settings

    # Deja la cache limpia para no afectar otras pruebas.
    get_settings.cache_clear()


def test_settings_use_default_application_timezone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica la zona horaria predeterminada de la aplicacion.

    La disponibilidad interpretara los horarios de apertura y cierre
    de las sedes utilizando esta zona horaria.
    """
    configure_required_environment(monkeypatch)
    monkeypatch.delenv(
        "APP_TIMEZONE",
        raising=False,
    )

    settings = Settings(_env_file=None)

    assert settings.app_timezone == "America/Argentina/Buenos_Aires"


def test_settings_read_application_timezone_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que APP_TIMEZONE permita cambiar la zona configurada.
    """
    configure_required_environment(monkeypatch)
    monkeypatch.setenv(
        "APP_TIMEZONE",
        "America/Argentina/Cordoba",
    )

    settings = Settings(_env_file=None)

    assert settings.app_timezone == "America/Argentina/Cordoba"


def test_settings_reject_invalid_application_timezone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que una zona horaria inexistente sea rechazada.
    """
    configure_required_environment(monkeypatch)
    monkeypatch.setenv(
        "APP_TIMEZONE",
        "America/Argentina/Invalid",
    )

    with pytest.raises(
        ValidationError,
        match="La zona horaria de la aplicacion no es valida",
    ):
        Settings(_env_file=None)
