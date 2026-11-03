from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Header, HTTPException, status

from app.api.dependencies import ReservationReminderServiceDependency
from app.core.config import get_settings

router = APIRouter(prefix="/internal/reminders", tags=["Internal"])


@router.post("", status_code=status.HTTP_200_OK)
def send_reservation_reminders(
    service: ReservationReminderServiceDependency,
    x_reminder_secret: str | None = Header(default=None),
) -> dict[str, int]:
    """Procesa recordatorios; este endpoint debe ejecutarse mediante cron."""
    settings = get_settings()
    if (
        not settings.reminder_internal_secret
        or x_reminder_secret != settings.reminder_internal_secret
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar la tarea interna.",
        )

    now = datetime.now(ZoneInfo(settings.app_timezone))
    return {"sent": service.send_upcoming_reminders(now=now)}
