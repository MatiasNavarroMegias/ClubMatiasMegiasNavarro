from pwdlib import PasswordHash


class PasswordHasher:
    """
    Administra el hashing y la verificacion de contrasenas.

    La implementacion utiliza la configuracion recomendada por pwdlib,
    que actualmente genera hashes mediante Argon2.
    """

    def __init__(
        self,
        password_hash: PasswordHash | None = None,
    ) -> None:
        """
        Inicializa el servicio de seguridad.

        Args:
            password_hash: Implementacion opcional utilizada para
                facilitar las pruebas automatizadas.
        """
        self.password_hash = password_hash or PasswordHash.recommended()

    def hash(self, password: str) -> str:
        """
        Genera un hash seguro para almacenar en PostgreSQL.

        Args:
            password: Contrasena validada recibida durante el registro.

        Returns:
            Hash seguro que incluye algoritmo, parametros y sal.
        """
        return self.password_hash.hash(password)

    def verify(
        self,
        password: str,
        stored_password_hash: str,
    ) -> bool:
        """
        Verifica una contrasena contra el hash almacenado.

        Esta operacion se utilizara posteriormente durante el login.

        Args:
            password: Contrasena ingresada por el usuario.
            stored_password_hash: Hash recuperado desde PostgreSQL.

        Returns:
            True cuando la contrasena coincide con el hash.
        """
        return self.password_hash.verify(
            password,
            stored_password_hash,
        )
