from collections.abc import Callable
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.repositories import (
    ReservationRepository,
    SportsSpaceRepository,
)
from app.schemas import AvailabilitySlotResponse


class AvailabilitySportsSpaceNotFoundError(Exception):
    """
    Indica que el espacio deportivo solicitado no existe.
    """


class AvailabilitySportsSpaceInactiveError(Exception):
    """
    Indica que el espacio deportivo se encuentra inactivo.
    """


class AvailabilityVenueInactiveError(Exception):
    """
    Indica que la sede del espacio se encuentra inactiva.
    """


class AvailabilityDateInPastError(Exception):
    """
    Indica que la fecha consultada es anterior a la fecha actual.
    """


class AvailabilityService:
    """
    Calcula los turnos disponibles de un espacio deportivo.

    El servicio combina el horario de la sede, la zona horaria de la
    aplicacion, el momento actual y las reservas confirmadas.
    """

    def __init__(
        self,
        sports_space_repository: SportsSpaceRepository,
        reservation_repository: ReservationRepository,
        timezone: ZoneInfo,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        """
        Inicializa el servicio con sus dependencias.

        Args:
            sports_space_repository: Repositorio utilizado para
                consultar el espacio deportivo.
            reservation_repository: Repositorio utilizado para obtener
                las reservas confirmadas.
            timezone: Zona horaria utilizada por la aplicacion.
            now_provider: Funcion opcional que devuelve el momento
                actual. Permite utilizar fechas controladas en pruebas.
        """
        self.sports_space_repository = sports_space_repository
        self.reservation_repository = reservation_repository
        self.timezone = timezone
        self.now_provider = now_provider or self._current_datetime

    def list_available_slots(
        self,
        *,
        sports_space_id: int,
        selected_date: date,
    ) -> list[AvailabilitySlotResponse]:
        """
        Devuelve los turnos disponibles de una fecha.

        Cada turno posee una duracion exacta de una hora y comienza
        en una hora completa. Los turnos pasados y aquellos ocupados
        por reservas confirmadas son excluidos.

        Args:
            sports_space_id: Identificador del espacio deportivo.
            selected_date: Fecha local que debe consultarse.

        Returns:
            Turnos disponibles ordenados por horario de inicio.

        Raises:
            AvailabilitySportsSpaceNotFoundError: Cuando el espacio
                no existe.
            AvailabilitySportsSpaceInactiveError: Cuando el espacio
                se encuentra inactivo.
            AvailabilityVenueInactiveError: Cuando la sede se
                encuentra inactiva.
            AvailabilityDateInPastError: Cuando la fecha consultada
                es anterior a la fecha actual.
        """
        sports_space = self.sports_space_repository.get_by_id(
            sports_space_id,
        )

        if sports_space is None:
            raise AvailabilitySportsSpaceNotFoundError(
                f"No existe un espacio deportivo con el identificador {sports_space_id}."
            )

        if not sports_space.is_active:
            raise AvailabilitySportsSpaceInactiveError(
                "El espacio deportivo se encuentra inactivo."
            )

        venue = sports_space.venue

        if not venue.is_active:
            raise AvailabilityVenueInactiveError(
                "La sede del espacio deportivo se encuentra inactiva."
            )

        current_datetime = self._get_current_datetime()

        if selected_date < current_datetime.date():
            raise AvailabilityDateInPastError(
                "No se puede consultar disponibilidad para una fecha pasada."
            )

        range_start = datetime.combine(
            selected_date,
            datetime.min.time(),
            tzinfo=self.timezone,
        )
        range_end = range_start + timedelta(days=1)

        confirmed_reservations = self.reservation_repository.list_confirmed_for_space_between(
            sports_space_id=sports_space_id,
            range_start=range_start,
            range_end=range_end,
        )

        first_slot_start = self._round_up_to_full_hour(
            datetime.combine(
                selected_date,
                venue.opening_time,
                tzinfo=self.timezone,
            )
        )
        closing_datetime = datetime.combine(
            selected_date,
            venue.closing_time,
            tzinfo=self.timezone,
        )

        available_slots: list[AvailabilitySlotResponse] = []
        slot_start = first_slot_start

        while slot_start + timedelta(hours=1) <= closing_datetime:
            slot_end = slot_start + timedelta(hours=1)

            if slot_start > current_datetime and not self._is_occupied(
                slot_start=slot_start,
                slot_end=slot_end,
                reservations=confirmed_reservations,
            ):
                available_slots.append(
                    AvailabilitySlotResponse(
                        start_at=slot_start,
                        end_at=slot_end,
                    )
                )

            slot_start = slot_end

        return available_slots

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
            Momento actual convertido a la zona de la aplicacion.

        Raises:
            ValueError: Cuando now_provider devuelve una fecha sin
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

    @staticmethod
    def _round_up_to_full_hour(
        value: datetime,
    ) -> datetime:
        """
        Redondea un horario hacia la siguiente hora completa.

        Si el horario ya se encuentra en una hora completa, se
        mantiene sin cambios.

        Ejemplos:

        - 08:00 se mantiene como 08:00.
        - 08:30 se convierte en 09:00.
        """
        if value.minute == 0 and value.second == 0 and value.microsecond == 0:
            return value

        return value.replace(
            minute=0,
            second=0,
            microsecond=0,
        ) + timedelta(hours=1)

    def _is_occupied(
        self,
        *,
        slot_start: datetime,
        slot_end: datetime,
        reservations: list,
    ) -> bool:
        """
        Indica si un turno se superpone con una reserva confirmada.

        Args:
            slot_start: Inicio del turno generado.
            slot_end: Finalizacion del turno generado.
            reservations: Reservas confirmadas del rango consultado.

        Returns:
            True cuando existe una superposicion.
        """
        for reservation in reservations:
            reservation_start = reservation.start_at.astimezone(
                self.timezone,
            )
            reservation_end = reservation.end_at.astimezone(
                self.timezone,
            )

            if reservation_start < slot_end and reservation_end > slot_start:
                return True

        return False
