from app.core.security import AccessTokenService, PasswordHasher
from app.models import User
from app.repositories import UserRepository
from app.schemas import UserLogin, UserRegister, UserUpdate


class EmailAlreadyRegisteredError(Exception):
    """
    Indica que el correo ya pertenece a una cuenta registrada.

    El servicio utiliza una excepcion propia para permanecer
    independiente de FastAPI y de los codigos HTTP.
    """


class InvalidCredentialsError(Exception):
    """
    Indica que el correo o la contrasena no son correctos.

    Se utiliza el mismo error para ambos casos con el objetivo de no
    revelar si una direccion de correo se encuentra registrada.
    """


class InactiveUserError(Exception):
    """
    Indica que una cuenta existente se encuentra desactivada.

    Una cuenta inactiva conserva sus datos y reservas, pero no puede
    iniciar una nueva sesion.
    """


class AuthService:
    """
    Aplica las reglas de negocio relacionadas con autenticacion.

    El servicio administra la registracion segura y el inicio de sesion
    sin depender de FastAPI ni de respuestas HTTP.
    """

    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
        access_token_service: AccessTokenService | None = None,
    ) -> None:
        """
        Inicializa el servicio con sus dependencias.

        Args:
            repository: Repositorio utilizado para consultar y guardar
                usuarios.
            password_hasher: Servicio encargado de proteger y verificar
                contrasenas.
            access_token_service: Servicio opcional encargado de crear
                tokens JWT. Es obligatorio para iniciar sesion, pero no
                para ejecutar exclusivamente el flujo de registracion.
        """
        self.repository = repository
        self.password_hasher = password_hasher
        self.access_token_service = access_token_service

    def register_user(
        self,
        registration_data: UserRegister,
    ) -> User:
        """
        Registra un usuario utilizando datos previamente validados.

        Args:
            registration_data: Datos validados y normalizados mediante
                UserRegister.

        Returns:
            Usuario persistido con identificador y fechas.

        Raises:
            EmailAlreadyRegisteredError: Cuando el correo ya pertenece
                a otra cuenta.
        """
        existing_user = self.repository.get_by_email(
            registration_data.email,
        )

        if existing_user is not None:
            raise EmailAlreadyRegisteredError("Ya existe un usuario registrado con ese correo.")

        password_hash = self.password_hasher.hash(
            registration_data.password,
        )

        user = User(
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            birth_date=registration_data.birth_date,
            email=registration_data.email,
            password_hash=password_hash,
            is_active=True,
        )

        return self.repository.add(user)

    def login_user(
        self,
        login_data: UserLogin,
    ) -> str:
        """
        Verifica las credenciales y genera un token de acceso.

        Args:
            login_data: Correo normalizado y contrasena recibida.

        Returns:
            Token JWT firmado para el usuario autenticado.

        Raises:
            InvalidCredentialsError: Cuando el correo no existe o la
                contrasena no coincide con el hash almacenado.
            InactiveUserError: Cuando la cuenta esta desactivada.
            RuntimeError: Cuando el servicio de tokens no fue configurado.
        """
        user = self.repository.get_by_email(
            login_data.email,
        )

        if user is None:
            raise InvalidCredentialsError("Correo o contrasena incorrectos.")

        password_matches = self.password_hasher.verify(
            login_data.password,
            user.password_hash,
        )

        if not password_matches:
            raise InvalidCredentialsError("Correo o contrasena incorrectos.")

        if not user.is_active:
            raise InactiveUserError("La cuenta de usuario se encuentra inactiva.")

        if self.access_token_service is None:
            raise RuntimeError("El servicio de tokens no se encuentra configurado.")

        return self.access_token_service.create_access_token(
            user_id=user.id,
        )

    def update_profile(
        self,
        user: User,
        update_data: UserUpdate,
    ) -> User:
        """
        Actualiza los campos editables del perfil autenticado.

        Args:
            user: Usuario obtenido desde la sesion autenticada.
            update_data: Campos validados que se desean modificar.

        Returns:
            Usuario actualizado.

        Raises:
            ValueError: Cuando no se envio ningun campo o cuando los
                valores coinciden con el perfil actual.
        """
        changes = update_data.model_dump(exclude_unset=True)

        if not changes:
            raise ValueError("Debe indicar al menos un campo para actualizar.")

        effective_changes = {
            field_name: value
            for field_name, value in changes.items()
            if getattr(user, field_name) != value
        }

        if not effective_changes:
            raise ValueError("Los datos enviados coinciden con el perfil actual.")

        for field_name, value in effective_changes.items():
            setattr(user, field_name, value)

        return self.repository.save(user)
