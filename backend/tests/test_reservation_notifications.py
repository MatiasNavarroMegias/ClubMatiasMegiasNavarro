from datetime import datetime, time
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from app.models import PushDevice, Reservation, SportsSpace, User, Venue
from app.repositories import PushDeviceRepository, ReservationRepository, SportsSpaceRepository
from app.schemas import ReservationCreate
from app.services import (
    ReservationNotificationService,
    ReservationReminderService,
    ReservationService,
)

APPLICATION_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")


def create_reservation() -> Reservation:
    venue = Venue(
        id=1,
        name="Sede Ramos Mejia",
        is_active=True,
        opening_time=time(8, 0),
        closing_time=time(23, 0),
    )
    sports_space = SportsSpace(
        id=8,
        name="Cancha de Futbol 1",
        is_active=True,
        venue=venue,
    )
    return Reservation(
        id=15,
        user_id=7,
        sports_space_id=8,
        start_at=datetime(2026, 11, 3, 18, 0, tzinfo=APPLICATION_TIMEZONE),
        end_at=datetime(2026, 11, 3, 19, 0, tzinfo=APPLICATION_TIMEZONE),
        status="confirmed",
        user=User(id=7, email="matias@example.com"),
        sports_space=sports_space,
    )


def test_created_reservation_sends_expected_message_to_active_devices() -> None:
    sender = MagicMock()
    device_repository = MagicMock(spec=PushDeviceRepository)
    device_repository.list_active_by_user_id.return_value = [
        PushDevice(installation_id="fid-1", user_id=7, platform="android", is_active=True),
    ]
    service = ReservationNotificationService(
        push_device_repository=device_repository,
        sender=sender,
    )

    service.notify_reservation_created(create_reservation())

    sender.send.assert_called_once_with(
        installation_id="fid-1",
        title="Reserva confirmada",
        body=("Sede Ramos Mejia - Cancha de Futbol 1, 03/11/2026 18:00 a 19:00."),
    )


def test_cancelled_reservation_sends_expected_message() -> None:
    sender = MagicMock()
    device_repository = MagicMock(spec=PushDeviceRepository)
    device_repository.list_active_by_user_id.return_value = []
    service = ReservationNotificationService(
        push_device_repository=device_repository,
        sender=sender,
    )

    service.notify_reservation_cancelled(create_reservation())

    sender.send.assert_not_called()


def test_reminder_marks_reservation_only_after_success_and_skips_duplicates() -> None:
    reservation = create_reservation()
    reservation_repository = MagicMock(spec=ReservationRepository)
    reservation_repository.list_confirmed_starting_between.return_value = [reservation]
    reminder_repository = MagicMock()
    reminder_repository.was_sent.return_value = True
    notification_service = MagicMock(spec=ReservationNotificationService)
    service = ReservationReminderService(
        reservation_repository=reservation_repository,
        reminder_repository=reminder_repository,
        notification_service=notification_service,
        timezone=APPLICATION_TIMEZONE,
    )

    sent_count = service.send_upcoming_reminders(
        now=datetime(2026, 11, 3, 17, 0, tzinfo=APPLICATION_TIMEZONE),
    )

    assert sent_count == 0
    notification_service.notify_reservation_reminder.assert_not_called()
    reminder_repository.mark_sent.assert_not_called()


def test_reminder_sends_one_hour_before_reservation() -> None:
    reservation = create_reservation()
    reservation_repository = MagicMock(spec=ReservationRepository)
    reservation_repository.list_confirmed_starting_between.return_value = [reservation]
    reminder_repository = MagicMock()
    reminder_repository.was_sent.return_value = False
    notification_service = MagicMock(spec=ReservationNotificationService)
    service = ReservationReminderService(
        reservation_repository=reservation_repository,
        reminder_repository=reminder_repository,
        notification_service=notification_service,
        timezone=APPLICATION_TIMEZONE,
    )

    sent_count = service.send_upcoming_reminders(
        now=datetime(2026, 11, 3, 17, 0, tzinfo=APPLICATION_TIMEZONE),
    )

    assert sent_count == 1
    notification_service.notify_reservation_reminder.assert_called_once_with(reservation)
    reminder_repository.mark_sent.assert_called_once_with(reservation.id)
    reservation_repository.list_confirmed_starting_between.assert_called_once_with(
        range_start=datetime(2026, 11, 3, 17, 55, tzinfo=APPLICATION_TIMEZONE),
        range_end=datetime(2026, 11, 3, 18, 5, tzinfo=APPLICATION_TIMEZONE),
    )


def test_reminder_is_not_marked_when_delivery_fails() -> None:
    reservation = create_reservation()
    reservation_repository = MagicMock(spec=ReservationRepository)
    reservation_repository.list_confirmed_starting_between.return_value = [reservation]
    reminder_repository = MagicMock()
    reminder_repository.was_sent.return_value = False
    notification_service = MagicMock(spec=ReservationNotificationService)
    notification_service.notify_reservation_reminder.return_value = False
    service = ReservationReminderService(
        reservation_repository=reservation_repository,
        reminder_repository=reminder_repository,
        notification_service=notification_service,
        timezone=APPLICATION_TIMEZONE,
    )

    sent_count = service.send_upcoming_reminders(
        now=datetime(2026, 11, 3, 17, 0, tzinfo=APPLICATION_TIMEZONE),
    )

    assert sent_count == 0
    reminder_repository.mark_sent.assert_not_called()


def test_reservation_creation_keeps_success_when_sender_fails() -> None:
    reservation_repository = MagicMock(spec=ReservationRepository)
    sports_space_repository = MagicMock(spec=SportsSpaceRepository)
    notification_service = MagicMock(spec=ReservationNotificationService)
    notification_service.notify_reservation_created.side_effect = RuntimeError(
        "Firebase unavailable",
    )
    sports_space_repository.get_by_id.return_value = create_reservation().sports_space
    reservation_repository.get_overlapping_confirmed.return_value = None
    reservation_repository.add.side_effect = lambda reservation: reservation
    service = ReservationService(
        reservation_repository=reservation_repository,
        sports_space_repository=sports_space_repository,
        timezone=APPLICATION_TIMEZONE,
        now_provider=lambda: datetime(2026, 11, 2, 10, 30, tzinfo=APPLICATION_TIMEZONE),
        notification_service=notification_service,
    )

    reservation = service.create_reservation(
        user_id=7,
        reservation_data=ReservationCreate(
            sports_space_id=8,
            start_at=datetime(2026, 11, 3, 18, 0, tzinfo=APPLICATION_TIMEZONE),
        ),
    )

    assert reservation.status == "confirmed"
    reservation_repository.add.assert_called_once()
