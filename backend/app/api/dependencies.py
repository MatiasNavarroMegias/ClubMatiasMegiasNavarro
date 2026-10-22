from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.security import PasswordHasher
from app.repositories import UserRepository, VenueRepository
from app.services import AuthService, VenueService

# Tipo reutilizable que representa una sesion administrada por FastAPI.
DatabaseSession = Annotated[Session, Depends(get_db_session)]


def get_auth_service(
    database_session: DatabaseSession,
) -> AuthService:
    """
    Construye el servicio de autenticacion para una solicitud HTTP.

    FastAPI obtiene una sesion de SQLAlchemy. Luego se construyen el
    repositorio de usuarios y el componente de hashing necesarios
    para aplicar las reglas de registracion.

    Args:
        database_session: Sesion asociada a la solicitud actual.

    Returns:
        Servicio preparado para registrar y autenticar usuarios.
    """
    repository = UserRepository(database_session)
    password_hasher = PasswordHasher()

    return AuthService(
        repository=repository,
        password_hasher=password_hasher,
    )


def get_venue_service(
    database_session: DatabaseSession,
) -> VenueService:
    """
    Construye el servicio de sedes para una solicitud HTTP.

    FastAPI obtiene una sesion mediante get_db_session. Luego esta
    funcion crea el repositorio y finalmente construye el servicio
    que contiene las reglas de negocio.

    Args:
        database_session: Sesion de SQLAlchemy asociada a la solicitud.

    Returns:
        Servicio preparado para administrar sedes.
    """
    repository = VenueRepository(database_session)

    return VenueService(repository)


# Tipo reutilizable para inyectar AuthService en los endpoints.
AuthServiceDependency = Annotated[
    AuthService,
    Depends(get_auth_service),
]


# Tipo reutilizable para inyectar VenueService en los endpoints.
VenueServiceDependency = Annotated[
    VenueService,
    Depends(get_venue_service),
]
