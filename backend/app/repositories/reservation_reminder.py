from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ReservationReminder


class ReservationReminderRepository:
    """Administra la marca de recordatorios ya enviados."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def was_sent(self, reservation_id: int) -> bool:
        statement = select(ReservationReminder.id).where(
            ReservationReminder.reservation_id == reservation_id,
        )
        return self.database_session.scalar(statement) is not None

    def mark_sent(self, reservation_id: int) -> ReservationReminder:
        reminder = ReservationReminder(reservation_id=reservation_id)
        self.database_session.add(reminder)
        self.database_session.commit()
        self.database_session.refresh(reminder)
        return reminder
