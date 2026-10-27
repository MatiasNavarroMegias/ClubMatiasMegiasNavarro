from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.security import (
    AccessTokenService,
    InvalidAccessTokenError,
    PasswordHasher,
)
from app.models import User
from app.repositories import (
    SportsSpaceRepository,
    UserRepository,
    VenueRepository,
)
from app.services import (
    AuthService,
    SportsSpaceService,
    VenueService,
)

# Tipo reutilizable que representa una sesion administrada por FastAPI.
DatabaseSession = Annotated[Session, Depends(get_db_session)]

# Extrae las credenciales Bearer desde el encabezado Authorization.
#
# Swagger muestra un unico campo para ingresar el JWT obtenido mediante
# POST /auth/login, que utiliza un cuerpo JSON.
bearer_scheme = HTTPBearer()


def get_access_token_service() -> AccessTokenService:
    """
    Construye el servicio encargado de validar y generar tokens JWT.

    Returns:
        Servicio configurado mediante variables de entorno.
    """
    settings = get_settings()

    return AccessTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.access_token_expire_minutes,
    )


def get_auth_service(
    database_session: DatabaseSession,
) -> AuthService:
    """
    Construye el servicio de autenticacion para una solicitud HTTP.

    FastAPI obtiene la sesion de SQLAlchemy y la configuracion validada.
    Luego construye el repositorio, el componente de hashing y el
    servicio encargado de crear tokens JWT.

    Args:
        database_session: Sesion asociada a la solicitud actual.

    Returns:
        Servicio preparado para registrar e iniciar sesion.
    """
    repository = UserRepository(database_session)
    password_hasher = PasswordHasher()
    access_token_service = get_access_token_service()

    return AuthService(
        repository=repository,
        password_hasher=password_hasher,
        access_token_service=access_token_service,
    )


def get_current_user(
    database_session: DatabaseSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
) -> User:
    """
    Obtiene el usuario autenticado mediante el token Bearer.

    El token se valida antes de consultar PostgreSQL. Luego se comprueba
    que la cuenta exista y permanezca activa.

    Args:
        database_session: Sesion asociada a la solicitud actual.
        credentials: Credenciales Bearer extraidas del encabezado
            Authorization.

    Returns:
        Usuario autenticado recuperado desde PostgreSQL.

    Raises:
        HTTPException: Con codigo 401 cuando el token no es valido,
            esta vencido o identifica una cuenta inexistente.
        HTTPException: Con codigo 403 cuando la cuenta esta inactiva.
    """
    access_token_service = get_access_token_service()
    repository = UserRepository(database_session)
    token = credentials.credentials

    try:
        user_id = access_token_service.get_user_id(token)
    except InvalidAccessTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar la sesion.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from error

    user = repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar la sesion.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario se encuentra inactiva.",
        )

    return user


def get_venue_service(
    database_session: DatabaseSession,
) -> VenueService:
    """
    Construye el servicio de sedes para una solicitud HTTP.

    Args:
        database_session: Sesion de SQLAlchemy asociada a la solicitud.

    Returns:
        Servicio preparado para administrar sedes.
    """
    repository = VenueRepository(database_session)

    return VenueService(repository)


def get_sports_space_service(
    database_session: DatabaseSession,
) -> SportsSpaceService:
    """
    Construye el servicio de espacios deportivos.

    La sesion actual se comparte entre los repositorios de espacios
    y sedes para mantener una unica transaccion por solicitud.

    Args:
        database_session: Sesion asociada a la solicitud HTTP.

    Returns:
        Servicio preparado para administrar espacios deportivos.
    """
    repository = SportsSpaceRepository(
        database_session,
    )
    venue_repository = VenueRepository(
        database_session,
    )

    return SportsSpaceService(
        repository=repository,
        venue_repository=venue_repository,
    )


# Tipo reutilizable para inyectar AuthService en los endpoints.
AuthServiceDependency = Annotated[
    AuthService,
    Depends(get_auth_service),
]

# Tipo reutilizable para inyectar el usuario autenticado.
CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

# Tipo reutilizable para inyectar VenueService en los endpoints.
VenueServiceDependency = Annotated[
    VenueService,
    Depends(get_venue_service),
]

# Tipo reutilizable para inyectar SportsSpaceService.
SportsSpaceServiceDependency = Annotated[
    SportsSpaceService,
    Depends(get_sports_space_service),
]
