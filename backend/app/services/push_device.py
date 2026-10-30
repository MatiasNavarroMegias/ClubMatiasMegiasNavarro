from app.models import PushDevice, User
from app.repositories import PushDeviceRepository


class PushDeviceService:
    """
    Aplica las reglas de negocio de las instalaciones push.

    El servicio registra nuevas instalaciones y mantiene actualizado
    el usuario, la plataforma y el estado de las ya existentes.
    """

    def __init__(
        self,
        repository: PushDeviceRepository,
    ) -> None:
        """
        Inicializa el servicio con su repositorio.

        Args:
            repository: Repositorio utilizado para consultar y
                persistir instalaciones push.
        """
        self.repository = repository

    def register(
        self,
        user: User,
        installation_id: str,
        platform: str,
    ) -> PushDevice:
        """
        Registra o actualiza una instalacion de Firebase.

        Si el identificador no existe, crea una instalacion asociada
        con el usuario autenticado. Si ya existe, actualiza solamente
        los datos que hayan cambiado.

        Args:
            user: Usuario autenticado propietario de la instalacion.
            installation_id: Identificador unico entregado por Firebase.
            platform: Plataforma desde la que se registra la aplicacion.

        Returns:
            Instalacion creada, actualizada o encontrada sin cambios.
        """
        existing_device = self.repository.get_by_installation_id(
            installation_id,
        )

        if existing_device is None:
            push_device = PushDevice(
                user_id=user.id,
                installation_id=installation_id,
                platform=platform,
                is_active=True,
            )

            return self.repository.add(push_device)

        has_changes = False

        if existing_device.user_id != user.id:
            existing_device.user_id = user.id
            has_changes = True

        if existing_device.platform != platform:
            existing_device.platform = platform
            has_changes = True

        if not existing_device.is_active:
            existing_device.is_active = True
            has_changes = True

        if has_changes:
            return self.repository.save(existing_device)

        return existing_device
