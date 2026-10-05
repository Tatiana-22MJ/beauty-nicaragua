# =============================================================================
# reminders.py — Recordatorio 24 h antes de cada cita (lógica reutilizable)
# =============================================================================
# La ejecución programada vive en scripts/send_reminders.py (CLI) y en
# .github/workflows/reminders.yml (cron diario 07:00 en Managua).

from datetime import timedelta

from availability import ACTIVE_STATUSES
from extensions import db
from models import Booking
from notifications import send_booking_reminder, whatsapp_link
from timeutils import now_ni, today_ni


def target_date() -> str:
    """Fecha de las citas a recordar (mañana en Nicaragua)."""
    return (today_ni() + timedelta(days=1)).strftime("%Y-%m-%d")


def collect_pending(date_str: str | None = None) -> list[Booking]:
    """Citas activas de la fecha objetivo sin recordatorio enviado."""
    date_str = date_str or target_date()
    return (
        Booking.query.filter(
            Booking.preferred_date == date_str,
            Booking.status.in_(ACTIVE_STATUSES),
            Booking.reminder_sent_at.is_(None),
        )
        .order_by(Booking.preferred_time)
        .all()
    )


def preview_link(booking: Booking) -> str:
    """Deep-link wa.me con el mensaje del recordatorio (fallback sin Twilio)."""
    return whatsapp_link(
        f"Hola {booking.full_name}, te recordamos tu cita de mañana "
        f"({booking.title} {booking.preferred_time}).",
        booking.phone,
    )


def send_pending(dry_run: bool = False) -> dict:
    """Envía los recordatorios pendientes. Requiere app context.

    Devuelve {"target": fecha, "pending": n, "sent": n, "failed": n}.
    """
    date_str = target_date()
    pending = collect_pending(date_str)
    result = {"target": date_str, "pending": len(pending), "sent": 0, "failed": 0}

    for booking in pending:
        if dry_run:
            print(f"[DRY-RUN] #{booking.id} {booking.full_name} → {preview_link(booking)}")
            continue
        if send_booking_reminder(booking):
            booking.reminder_sent_at = now_ni().replace(tzinfo=None)
            db.session.commit()
            result["sent"] += 1
            print(f"[OK] #{booking.id} → {booking.full_name} ({booking.phone})")
        else:
            result["failed"] += 1
            print(f"[FALLO] #{booking.id} → {booking.full_name}")

    return result
