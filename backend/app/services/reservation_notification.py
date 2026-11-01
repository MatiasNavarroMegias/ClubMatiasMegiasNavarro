import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.models import Reservation
from app.repositories import (
    PushDeviceRepository,
    ReservationReminderRepository,
    ReservationRepository,
)
from app.services.firebase_push_sender import FirebasePushSender

logger = logging.getLogger(__name__)


class ReservationNotificationService:
    """Construye y envia avisos relacionados con reservas."""

    def __init__(
        self,
        *,
        push_device_repository: PushDeviceRepository,
        sender: FirebasePushSender,
    ) -> None:
        self.push_device_repository = push_device_repository
        self.sender = sender

    def notify_reservation_created(self, reservation: Reservation) -> bool:
        return self._notify(
            reservation=reservation,
            title="Reserva confirmada",
            body=self._reservation_body(reservation),
        )

    def notify_reservation_cancelled(self, reservation: Reservation) -> bool:
        return self._notify(
            reservation=reservation,
            title="Reserva cancelada",
            body=self._reservation_body(reservation),
        )

    def notify_reservation_reminder(self, reservation: Reservation) -> bool:
        return self._notify(
            reservation=reservation,
            title="Recordatorio de reserva",
            body=(f"Tu reserva en {reservation.sports_space.name} comienza dentro de una hora."),
        )

    def _notify(
        self,
        *,
        reservation: Reservation,
        title: str,
        body: str,
    ) -> bool:
        devices = self.push_device_repository.list_active_by_user_id(
            reservation.user_id,
        )
        all_sent = True

        for device in devices:
            try:
                self.sender.send(
                    installation_id=device.installation_id,
                    title=title,
                    body=body,
                )
            except Exception:
                all_sent = False
                logger.exception(
                    "No se pudo enviar una notificacion de reserva.",
                    extra={"push_device_id": device.id, "reservation_id": reservation.id},
                )
        return all_sent

    @staticmethod
    def _reservation_body(reservation: Reservation) -> str:
        start_at = reservation.start_at
        end_at = reservation.end_at
        return (
            f"{reservation.sports_space.venue.name} - "
            f"{reservation.sports_space.name}, "
            f"{_format_datetime(start_at)} a {_format_time(end_at)}."
        )


class ReservationReminderService:
    """Procesa recordatorios una hora antes de cada reserva."""

    def __init__(
        self,
        *,
        reservation_repository: ReservationRepository,
        reminder_repository: ReservationReminderRepository,
        notification_service: ReservationNotificationService,
        timezone: ZoneInfo,
    ) -> None:
        self.reservation_repository = reservation_repository
        self.reminder_repository = reminder_repository
        self.notification_service = notification_service
        self.timezone = timezone

    def send_upcoming_reminders(self, *, now: datetime) -> int:
        range_start = now.astimezone(self.timezone).replace(second=0, microsecond=0)
        range_start += timedelta(minutes=55)
        range_end = range_start + timedelta(minutes=10)
        reservations = self.reservation_repository.list_confirmed_starting_between(
            range_start=range_start,
            range_end=range_end,
        )

        sent_count = 0
        for reservation in reservations:
            if self.reminder_repository.was_sent(reservation.id):
                continue

            if self.notification_service.notify_reservation_reminder(reservation):
                self.reminder_repository.mark_sent(reservation.id)
                sent_count += 1

        return sent_count


def _format_datetime(value: datetime) -> str:
    return value.strftime("%d/%m/%Y %H:%M")


def _format_time(value: datetime) -> str:
    return value.strftime("%H:%M")
