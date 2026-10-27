from collections.abc import Callable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.models import Reservation
from app.repositories import (
    ReservationRepository,
    SportsSpaceRepository,
)
from app.schemas import ReservationCreate


class ReservationSportsSpaceNotFoundError(Exception):
    """
    Indica que el espacio deportivo solicitado no existe.
    """


class ReservationSportsSpaceInactiveError(Exception):
    """
    Indica que el espacio deportivo se encuentra inactivo.
    """


class ReservationVenueInactiveError(Exception):
    """
    Indica que la sede del espacio se encuentra inactiva.
    """


class ReservationStartInPastError(Exception):
    """
    Indica que el horario solicitado no pertenece al futuro.
    """


class ReservationInvalidStartTimeError(Exception):
    """
    Indica que el turno no comienza en una hora completa.
    """


class ReservationOutsideVenueHoursError(Exception):
    """
    Indica que el turno queda fuera del horario de la sede.
    """


class ReservationTimeConflictError(Exception):
    """
    Indica que el turno se superpone con otra reserva confirmada.
    """


class ReservationNotFoundError(Exception):
    """
    Indica que la reserva no existe o no pertenece al usuario.
    """


class ReservationAlreadyCancelledError(Exception):
    """
    Indica que la reserva ya fue cancelada anteriormente.
    """


class ReservationAlreadyStartedError(Exception):
    """
    Indica que la reserva ya comenzo y no puede cancelarse.
    """


class ReservationService:
    """
    Aplica las reglas de negocio necesarias para crear reservas.

    El servicio valida el espacio, la sede, el horario solicitado y
    las reservas confirmadas antes de guardar el nuevo turno.
    """

    def __init__(
        self,
        reservation_repository: ReservationRepository,
        sports_space_repository: SportsSpaceRepository,
        timezone: ZoneInfo,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        """
        Inicializa el servicio con sus dependencias.

        Args:
            reservation_repository: Repositorio utilizado para
                consultar y guardar reservas.
            sports_space_repository: Repositorio utilizado para
                consultar el espacio deportivo.
            timezone: Zona horaria utilizada por la aplicacion.
            now_provider: Funcion opcional que devuelve el momento
                actual. Permite utilizar un reloj fijo en las pruebas.
        """
        self.reservation_repository = reservation_repository
        self.sports_space_repository = sports_space_repository
        self.timezone = timezone
        self.now_provider = now_provider or self._current_datetime

    def create_reservation(
        self,
        *,
        user_id: int,
        reservation_data: ReservationCreate,
    ) -> Reservation:
        """
        Crea una reserva confirmada de una hora completa.

        El usuario se recibe desde la sesion autenticada y no desde el
        cuerpo de la solicitud. El horario final se calcula sumando una
        hora al inicio solicitado.

        Args:
            user_id: Identificador del usuario autenticado.
            reservation_data: Espacio y horario solicitados.

        Returns:
            Reserva confirmada y persistida.

        Raises:
            ReservationSportsSpaceNotFoundError: Cuando el espacio no
                existe.
            ReservationSportsSpaceInactiveError: Cuando el espacio se
                encuentra inactivo.
            ReservationVenueInactiveError: Cuando la sede se encuentra
                inactiva.
            ReservationStartInPastError: Cuando el horario no pertenece
                al futuro.
            ReservationInvalidStartTimeError: Cuando el horario no
                comienza en una hora completa.
            ReservationOutsideVenueHoursError: Cuando el turno queda
                fuera del horario de la sede.
            ReservationTimeConflictError: Cuando existe una reserva
                confirmada superpuesta.
        """
        sports_space = self.sports_space_repository.get_by_id(
            reservation_data.sports_space_id,
        )

        if sports_space is None:
            raise ReservationSportsSpaceNotFoundError(
                "No existe un espacio deportivo con el "
                f"identificador {reservation_data.sports_space_id}."
            )

        if not sports_space.is_active:
            raise ReservationSportsSpaceInactiveError("El espacio deportivo se encuentra inactivo.")

        venue = sports_space.venue

        if not venue.is_active:
            raise ReservationVenueInactiveError(
                "La sede del espacio deportivo se encuentra inactiva."
            )

        start_at = self._normalize_datetime(
            reservation_data.start_at,
        )
        current_datetime = self._get_current_datetime()

        if start_at <= current_datetime:
            raise ReservationStartInPastError("El horario de la reserva debe pertenecer al futuro.")

        if not self._starts_on_full_hour(start_at):
            raise ReservationInvalidStartTimeError("La reserva debe comenzar en una hora completa.")

        end_at = start_at + timedelta(hours=1)

        opening_datetime = datetime.combine(
            start_at.date(),
            venue.opening_time,
            tzinfo=self.timezone,
        )
        closing_datetime = datetime.combine(
            start_at.date(),
            venue.closing_time,
            tzinfo=self.timezone,
        )

        if start_at < opening_datetime or end_at > closing_datetime:
            raise ReservationOutsideVenueHoursError(
                "El turno solicitado se encuentra fuera del horario de funcionamiento de la sede."
            )

        overlapping_reservation = self.reservation_repository.get_overlapping_confirmed(
            sports_space_id=sports_space.id,
            start_at=start_at,
            end_at=end_at,
        )

        if overlapping_reservation is not None:
            raise ReservationTimeConflictError("El turno solicitado ya se encuentra reservado.")

        reservation = Reservation(
            user_id=user_id,
            sports_space_id=sports_space.id,
            start_at=start_at,
            end_at=end_at,
            status="confirmed",
            cancelled_at=None,
        )

        return self.reservation_repository.add(
            reservation,
        )

    def list_upcoming_reservations(
        self,
        *,
        user_id: int,
    ) -> list[Reservation]:
        """
        Devuelve las proximas reservas confirmadas del usuario.

        El momento actual se normaliza a la zona horaria configurada
        antes de enviarlo al repositorio.

        Args:
            user_id: Identificador del usuario autenticado.

        Returns:
            Reservas confirmadas ordenadas desde la mas cercana.
        """
        current_datetime = self._get_current_datetime()

        return self.reservation_repository.list_upcoming_by_user(
            user_id=user_id,
            from_at=current_datetime,
        )

    def list_reservation_history(
        self,
        *,
        user_id: int,
    ) -> list[Reservation]:
        """
        Devuelve el historial de reservas del usuario.

        El historial incluye reservas canceladas y reservas
        confirmadas cuyo horario ya finalizo.

        Args:
            user_id: Identificador del usuario autenticado.

        Returns:
            Historial ordenado desde la reserva mas reciente.
        """
        current_datetime = self._get_current_datetime()

        return self.reservation_repository.list_history_by_user(
            user_id=user_id,
            before_at=current_datetime,
        )

    def cancel_reservation(
        self,
        *,
        reservation_id: int,
        user_id: int,
    ) -> Reservation:
        """
        Cancela una reserva futura perteneciente al usuario.

        La reserva no se elimina. Su estado cambia a cancelled y se
        registra el momento exacto de la cancelacion.

        Args:
            reservation_id: Identificador de la reserva.
            user_id: Identificador del usuario autenticado.

        Returns:
            Reserva cancelada y persistida.

        Raises:
            ReservationNotFoundError: Cuando la reserva no existe o no
                pertenece al usuario.
            ReservationAlreadyCancelledError: Cuando la reserva ya se
                encuentra cancelada.
            ReservationAlreadyStartedError: Cuando el turno ya comenzo.
        """
        reservation = self.reservation_repository.get_by_id_and_user(
            reservation_id=reservation_id,
            user_id=user_id,
        )

        if reservation is None:
            raise ReservationNotFoundError(
                "No existe una reserva con el identificador "
                f"{reservation_id} para el usuario autenticado."
            )

        if reservation.status == "cancelled":
            raise ReservationAlreadyCancelledError("La reserva ya se encuentra cancelada.")

        current_datetime = self._get_current_datetime()
        reservation_start = self._normalize_datetime(
            reservation.start_at,
        )

        if reservation_start <= current_datetime:
            raise ReservationAlreadyStartedError("No se puede cancelar una reserva que ya comenzo.")

        reservation.status = "cancelled"
        reservation.cancelled_at = current_datetime

        return self.reservation_repository.save(
            reservation,
        )

    def _current_datetime(self) -> datetime:
        """
        Devuelve el momento actual en la zona de la aplicacion.
        """
        return datetime.now(
            self.timezone,
        )

    def _get_current_datetime(self) -> datetime:
        """
        Obtiene y normaliza el momento actual.

        Returns:
            Momento actual convertido a la zona configurada.

        Raises:
            ValueError: Cuando el proveedor devuelve una fecha sin
                zona horaria.
        """
        current_datetime = self.now_provider()

        if current_datetime.tzinfo is None or current_datetime.utcoffset() is None:
            raise ValueError(
                "El proveedor de fecha actual debe devolver una fecha con zona horaria."
            )

        return current_datetime.astimezone(
            self.timezone,
        )

    def _normalize_datetime(
        self,
        value: datetime,
    ) -> datetime:
        """
        Convierte una fecha a la zona horaria de la aplicacion.

        Args:
            value: Fecha recibida desde el esquema de creacion.

        Returns:
            Fecha convertida a la zona horaria configurada.

        Raises:
            ValueError: Cuando la fecha no incluye zona horaria.
        """
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("La fecha de inicio debe incluir una zona horaria.")

        return value.astimezone(
            self.timezone,
        )

    @staticmethod
    def _starts_on_full_hour(
        value: datetime,
    ) -> bool:
        """
        Indica si una fecha comienza exactamente en una hora completa.

        Minutos, segundos y microsegundos deben ser iguales a cero.
        """
        return value.minute == 0 and value.second == 0 and value.microsecond == 0
