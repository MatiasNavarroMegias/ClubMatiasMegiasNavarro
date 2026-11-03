from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

# Obtiene la configuracion validada del backend.
#
# DATABASE_URL se carga desde el archivo .env durante el desarrollo
# local y desde variables de entorno cuando la API se despliegue.
settings = get_settings()


# El motor administra las conexiones entre SQLAlchemy y PostgreSQL.
#
# pool_pre_ping comprueba que una conexion siga activa antes de
# reutilizarla. Esto ayuda a recuperar conexiones que fueron cerradas
# por PostgreSQL o por el proveedor de infraestructura.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


# SessionLocal funciona como una fabrica de sesiones.
#
# Cada operacion o solicitud HTTP utilizara su propia sesion para
# consultar o modificar datos dentro de PostgreSQL.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Clase base para los modelos persistentes de SQLAlchemy.

    Los futuros modelos, como Sede, Usuario o Reserva, heredaran
    de esta clase para que SQLAlchemy pueda reconocerlos y administrar
    su relacion con las tablas de PostgreSQL.
    """


def get_db_session() -> Generator[Session]:
    """
    Entrega una sesion de base de datos y garantiza su cierre.

    FastAPI utilizara esta funcion como dependencia. Cada solicitud
    recibira una sesion independiente y el bloque finally la cerrara
    incluso cuando ocurra una excepcion.

    Yields:
        Una sesion activa de SQLAlchemy.
    """
    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()
