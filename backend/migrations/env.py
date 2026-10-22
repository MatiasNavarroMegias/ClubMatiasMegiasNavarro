from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.core.database import Base

# Importa los modelos para registrarlos dentro de Base.metadata.
#
# Las clases no se utilizan directamente en este archivo, pero sus
# importaciones permiten que Alembic detecte las tablas automaticamente.
from app.models import User, Venue  # noqa: F401

# Obtiene el objeto de configuracion creado por Alembic.
#
# Este objeto permite leer alembic.ini y compartir configuraciones
# entre los comandos de migracion.
config = context.config


# Configura el sistema de logs definido dentro de alembic.ini.
#
# La validacion evita intentar cargar un archivo cuando Alembic
# se ejecuta desde un contexto que no posee configuracion externa.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Obtiene la configuracion validada de la aplicacion.
#
# Alembic utiliza la misma DATABASE_URL que el backend, evitando
# duplicar credenciales o mantener dos configuraciones diferentes.
settings = get_settings()


# ConfigParser interpreta el simbolo % como una expresion especial.
#
# Reemplazarlo por %% permite utilizar contrasenas codificadas que
# puedan contener porcentajes dentro de DATABASE_URL.
database_url = settings.database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url)


# Contiene los metadatos de todos los modelos SQLAlchemy.
#
# Alembic compara estos metadatos con la estructura existente en
# PostgreSQL para detectar tablas, columnas y restricciones nuevas.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Ejecuta migraciones sin abrir una conexion directa.

    Este modo genera instrucciones SQL utilizando solamente la URL
    configurada. Puede utilizarse para revisar o exportar scripts antes
    de aplicarlos sobre una base de datos.
    """
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Ejecuta migraciones mediante una conexion real con PostgreSQL.

    Alembic crea temporalmente un motor a partir de la configuracion,
    abre una conexion, ejecuta las migraciones pendientes y finalmente
    cierra los recursos utilizados.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Alembic decide automaticamente que estrategia utilizar segun
# la forma en que se ejecuto el comando.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
