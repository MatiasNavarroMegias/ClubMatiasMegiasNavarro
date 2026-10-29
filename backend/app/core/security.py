import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError as PyJWTInvalidTokenError
from pwdlib import PasswordHash


class InvalidAccessTokenError(Exception):
    """
    Indica que un token no puede utilizarse para autenticar al usuario.

    La excepcion evita propagar detalles internos de PyJWT hacia las
    capas de servicio o HTTP.
    """


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


class RecoveryCodeService:
    """
    Genera y protege codigos de recuperacion de contrasena.

    Los codigos se generan utilizando el modulo secrets. PostgreSQL
    recibe solamente un resumen HMAC SHA-256 y nunca el codigo original.
    """

    def __init__(
        self,
        secret_key: str,
        code_length: int = 8,
    ) -> None:
        """
        Inicializa el servicio de codigos temporales.

        Args:
            secret_key: Clave privada utilizada para calcular el HMAC.
            code_length: Cantidad de digitos del codigo generado.

        Raises:
            ValueError: Cuando la clave esta vacia o la longitud no
                permite generar un codigo razonable.
        """
        normalized_secret_key = secret_key.strip()

        if not normalized_secret_key:
            raise ValueError("La clave de recuperacion no puede estar vacia.")

        if code_length < 6:
            raise ValueError("El codigo de recuperacion debe tener al menos seis digitos.")

        self.secret_key = normalized_secret_key
        self.code_length = code_length

    def generate_code(self) -> str:
        """
        Genera un codigo numerico mediante un generador seguro.

        Returns:
            Codigo numerico con longitud fija.
        """
        limit = pow(
            10,
            self.code_length,
        )
        generated_number = secrets.randbelow(limit)

        return str(generated_number).zfill(
            self.code_length,
        )

    def create_digest(
        self,
        code: str,
    ) -> str:
        """
        Calcula el resumen HMAC SHA-256 de un codigo.

        Args:
            code: Codigo recibido o generado.

        Returns:
            Resumen hexadecimal de 64 caracteres.
        """
        return hmac.new(
            self.secret_key.encode("utf-8"),
            code.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify_code(
        self,
        code: str,
        stored_digest: str,
    ) -> bool:
        """
        Compara un codigo con el resumen almacenado.

        compare_digest evita comparaciones vulnerables a diferencias
        de tiempo observables.

        Args:
            code: Codigo introducido por el usuario.
            stored_digest: Resumen recuperado desde PostgreSQL.

        Returns:
            True cuando el codigo coincide.
        """
        received_digest = self.create_digest(
            code,
        )

        return hmac.compare_digest(
            received_digest,
            stored_digest,
        )


class AccessTokenService:
    """
    Genera y verifica tokens JWT utilizados para autenticar usuarios.

    Los tokens contienen solamente el identificador del usuario y las
    fechas necesarias para controlar su emision y vencimiento.
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        expire_minutes: int,
    ) -> None:
        """
        Inicializa el servicio con la configuracion del entorno.

        Args:
            secret_key: Clave utilizada para firmar y verificar tokens.
            algorithm: Algoritmo de firma permitido.
            expire_minutes: Duracion del token de acceso en minutos.
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    def create_access_token(
        self,
        user_id: int,
        *,
        issued_at: datetime | None = None,
    ) -> str:
        """
        Crea un token firmado para identificar a un usuario.

        Args:
            user_id: Identificador del usuario autenticado.
            issued_at: Fecha de emision opcional para facilitar pruebas.

        Returns:
            Token JWT firmado.

        El claim sub se almacena como texto porque esa es la
        representacion estandar esperada para el subject del token.
        """
        issued_at = issued_at or datetime.now(UTC)
        expires_at = issued_at + timedelta(
            minutes=self.expire_minutes,
        )

        payload = {
            "sub": str(user_id),
            "iat": issued_at,
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

    def get_user_id(self, token: str) -> int:
        """
        Verifica el token y devuelve el identificador del usuario.

        Args:
            token: Token recibido mediante Authorization Bearer.

        Returns:
            Identificador almacenado dentro del claim sub.

        Raises:
            InvalidAccessTokenError: Cuando la firma, la expiracion o
                el identificador contenido en el token no son validos.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )

            subject = payload.get("sub")

            if not isinstance(subject, str):
                raise InvalidAccessTokenError("El token de acceso no contiene un usuario valido.")

            user_id = int(subject)

            if user_id <= 0:
                raise InvalidAccessTokenError("El token de acceso no contiene un usuario valido.")

            return user_id
        except InvalidAccessTokenError:
            raise
        except (PyJWTInvalidTokenError, TypeError, ValueError) as error:
            raise InvalidAccessTokenError("El token de acceso es invalido o ha vencido.") from error
