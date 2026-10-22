from app.core.security import PasswordHasher
from app.models import User
from app.repositories import UserRepository
from app.schemas import UserRegister


class EmailAlreadyRegisteredError(Exception):
    """
    Indica que el correo ya pertenece a una cuenta registrada.

    El servicio utiliza una excepcion propia para permanecer
    independiente de FastAPI y de los codigos HTTP.
    """


class AuthService:
    """
    Aplica las reglas de negocio relacionadas con autenticacion.

    Durante el registro, el servicio comprueba el correo, genera un
    hash seguro y entrega el usuario al repositorio.
    """

    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        """
        Inicializa el servicio con sus dependencias.

        Args:
            repository: Repositorio utilizado para consultar y guardar
                usuarios.
            password_hasher: Servicio encargado de proteger contrasenas.
        """
        self.repository = repository
        self.password_hasher = password_hasher

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
