from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    """
    Administra las operaciones de persistencia de los usuarios.

    El repositorio concentra las consultas SQLAlchemy relacionadas
    con usuarios y no implementa reglas de registro o autenticacion.
    """

    def __init__(self, database_session: Session) -> None:
        """
        Inicializa el repositorio con una sesion de SQLAlchemy.

        Args:
            database_session: Sesion utilizada para consultar y
                persistir usuarios en PostgreSQL.
        """
        self.database_session = database_session

    def get_by_email(self, email: str) -> User | None:
        """
        Busca un usuario mediante su correo normalizado.

        Args:
            email: Correo electronico expresado en minusculas.

        Returns:
            El usuario encontrado o None cuando no existe.
        """
        statement = select(User).where(User.email == email)

        return self.database_session.scalar(statement)

    def add(self, user: User) -> User:
        """
        Persiste un usuario y recupera los valores generados.

        Args:
            user: Usuario que ya contiene un hash seguro de contrasena.

        Returns:
            Usuario actualizado con identificador y fechas.
        """
        self.database_session.add(user)
        self.database_session.commit()
        self.database_session.refresh(user)

        return user
