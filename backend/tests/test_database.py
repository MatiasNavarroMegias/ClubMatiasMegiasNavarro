from unittest.mock import MagicMock

import pytest

import app.core.database as database_module


def test_get_db_session_closes_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verifica que la sesion se cierre despues de ser utilizada.

    La prueba reemplaza temporalmente SessionLocal por una funcion
    controlada. De esta forma, no abre una conexion real con PostgreSQL
    ni depende de credenciales locales.
    """
    fake_session = MagicMock()

    # Reemplaza temporalmente la fabrica real de sesiones.
    monkeypatch.setattr(
        database_module,
        "SessionLocal",
        lambda: fake_session,
    )

    session_generator = database_module.get_db_session()

    # next ejecuta el generador hasta yield y obtiene la sesion.
    yielded_session = next(session_generator)

    assert yielded_session is fake_session

    # Continuar el generador ejecuta el bloque finally y lo finaliza.
    with pytest.raises(StopIteration):
        next(session_generator)

    fake_session.close.assert_called_once()
