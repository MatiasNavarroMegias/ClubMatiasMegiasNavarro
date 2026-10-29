from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import (
    AuthServiceDependency,
    PasswordRecoveryServiceDependency,
)
from app.schemas import (
    PasswordRecoveryConfirm,
    PasswordRecoveryMessage,
    PasswordRecoveryRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidPasswordRecoveryCodeError,
    PasswordRecoveryAttemptsExceededError,
)

# Agrupa los endpoints relacionados con autenticacion.
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    registration_data: UserRegister,
    service: AuthServiceDependency,
) -> UserResponse:
    """
    Registra un usuario utilizando datos previamente validados.

    El esquema valida y normaliza los datos. El servicio comprueba
    si el correo ya existe, genera un hash Argon2 y persiste la cuenta.

    Raises:
        HTTPException: Con codigo 409 cuando el correo ya pertenece
            a otra cuenta.
    """
    try:
        user = service.register_user(
            registration_data,
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return UserResponse.model_validate(
        user,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login_user(
    login_data: UserLogin,
    service: AuthServiceDependency,
) -> TokenResponse:
    """
    Inicia sesion mediante correo electronico y contrasena.

    El servicio busca la cuenta, verifica el hash Argon2, comprueba
    que el usuario se encuentre activo y genera un token JWT.

    Raises:
        HTTPException: Con codigo 401 para credenciales incorrectas.
        HTTPException: Con codigo 403 para una cuenta inactiva.
    """
    try:
        access_token = service.login_user(
            login_data,
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from error
    except InactiveUserError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    return TokenResponse(
        access_token=access_token,
    )


@router.post(
    "/password-recovery/request",
    response_model=PasswordRecoveryMessage,
    status_code=status.HTTP_200_OK,
)
def request_password_recovery(
    recovery_data: PasswordRecoveryRequest,
    service: PasswordRecoveryServiceDependency,
) -> PasswordRecoveryMessage:
    """
    Solicita un codigo temporal de recuperacion de contrasena.

    La respuesta publica es siempre la misma, independientemente de
    que el correo exista, no exista o pertenezca a una cuenta inactiva.
    Esto evita revelar que usuarios se encuentran registrados.

    Durante el desarrollo, el codigo se muestra en la consola del
    backend mediante DevelopmentRecoveryCodeNotifier.
    """
    message = service.request_recovery(
        recovery_data,
    )

    return PasswordRecoveryMessage(
        message=message,
    )


@router.post(
    "/password-recovery/confirm",
    response_model=PasswordRecoveryMessage,
    status_code=status.HTTP_200_OK,
)
def confirm_password_recovery(
    confirmation_data: PasswordRecoveryConfirm,
    service: PasswordRecoveryServiceDependency,
) -> PasswordRecoveryMessage:
    """
    Confirma el codigo temporal y establece una nueva contrasena.

    El servicio controla el vencimiento, la cantidad de intentos, el
    uso unico del codigo y el hashing seguro de la nueva contrasena.

    Raises:
        HTTPException: Con codigo 400 cuando el codigo no existe, no
            coincide, ya fue utilizado o se encuentra vencido.
        HTTPException: Con codigo 429 cuando el codigo alcanzo la
            cantidad maxima de intentos permitidos.
    """
    try:
        message = service.confirm_recovery(
            confirmation_data,
        )
    except PasswordRecoveryAttemptsExceededError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(error),
        ) from error
    except InvalidPasswordRecoveryCodeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return PasswordRecoveryMessage(
        message=message,
    )
