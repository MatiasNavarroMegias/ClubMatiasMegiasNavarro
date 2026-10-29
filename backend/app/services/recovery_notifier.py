from typing import Protocol


class RecoveryCodeNotifier(Protocol):
    """
    Define el mecanismo utilizado para entregar un codigo.

    El servicio de recuperacion depende de esta abstraccion y no de
    una tecnologia especifica como SMTP o un proveedor externo.
    """

    def send_recovery_code(
        self,
        email: str,
        code: str,
    ) -> None:
        """
        Entrega un codigo de recuperacion al correo indicado.

        Args:
            email: Correo normalizado del usuario.
            code: Codigo temporal generado para la recuperacion.
        """


class DevelopmentRecoveryCodeNotifier:
    """
    Muestra el codigo de recuperacion en la consola de desarrollo.

    Esta implementacion facilita probar el flujo completo localmente
    sin configurar credenciales de correo. No debe utilizarse en el
    entorno de produccion.
    """

    def send_recovery_code(
        self,
        email: str,
        code: str,
    ) -> None:
        """
        Muestra el codigo temporal en la consola.

        Args:
            email: Correo normalizado del usuario.
            code: Codigo temporal generado.
        """
        print(f"[PASSWORD RECOVERY] Email: {email} | Code: {code}")
