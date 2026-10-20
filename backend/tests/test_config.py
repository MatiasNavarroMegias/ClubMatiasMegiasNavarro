import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_read_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifica que la configuracion lea y convierta variables de entorno.

    monkeypatch permite definir variables temporales solamente durante
    esta prueba. De esta forma, la prueba no depende del archivo .env
    ni utiliza credenciales reales de PostgreSQL.
    """
    monkeypatch.setenv("APP_NAME", "API de prueba")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test_database",
    )

    settings = Settings(_env_file=None)

    assert settings.app_name == "API de prueba"
    assert settings.app_env == "testing"
    assert settings.app_debug is True
    assert settings.database_url.endswith("/test_database")


def test_settings_reject_invalid_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que un entorno desconocido produzca un error de validacion.

    La propiedad app_env acepta solamente development, testing o
    production. Esta restriccion evita iniciar la API con una
    configuracion escrita incorrectamente.
    """
    monkeypatch.setenv("APP_ENV", "invalid")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test_database",
    )

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
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("APP_DEBUG", "false")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test_database",
    )

    # Limpia cualquier instancia creada por pruebas o ejecuciones anteriores.
    get_settings.cache_clear()

    first_settings = get_settings()
    second_settings = get_settings()

    assert first_settings is second_settings

    # Deja la cache limpia para no afectar otras pruebas.
    get_settings.cache_clear()
