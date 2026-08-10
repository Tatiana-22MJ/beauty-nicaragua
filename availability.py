# =============================================================================
# availability.py — Generación y validación de horarios disponibles
# =============================================================================

from datetime import datetime, time, timedelta

from models import Booking

# Horarios operativos Managua (alineados a SalonInfo).
WEEKDAY_START = time(8, 0)
WEEKDAY_END = time(18, 0)
SATURDAY_START = time(8, 0)
SATURDAY_END = time(14, 0)
SLOT_MINUTES = 60  # Granularidad de la agenda.
ACTIVE_STATUSES = ("pending", "confirmed", "reschedule")  # Ocupan el hueco.


def _iter_slots(start: time, end: time, step_minutes: int = SLOT_MINUTES):
    """Genera strings HH:MM desde start inclusive hasta end exclusive."""
    cursor = datetime.combine(datetime.today().date(), start)
    limit = datetime.combine(datetime.today().date(), end)
    while cursor < limit:
        yield cursor.strftime("%H:%M")
        cursor += timedelta(minutes=step_minutes)


def day_window(date_str: str) -> tuple[time, time] | None:
    """Devuelve (inicio, fin) del día o None si está cerrado (domingo)."""
    try:
        day = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None
    weekday = day.weekday()  # 0=lunes … 6=domingo
    if weekday == 6:  # Domingo cerrado.
        return None
    if weekday == 5:  # Sábado.
        return SATURDAY_START, SATURDAY_END
    return WEEKDAY_START, WEEKDAY_END


def booked_times(date_str: str, exclude_booking_id: int | None = None) -> set[str]:
    """Horarios ya tomados en una fecha (pending/confirmed/reschedule)."""
    query = Booking.query.filter(
        Booking.preferred_date == date_str,
        Booking.status.in_(ACTIVE_STATUSES),
    )
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    return {b.preferred_time for b in query.all() if b.preferred_time}


def available_slots(date_str: str, exclude_booking_id: int | None = None) -> list[str]:
    """Lista de HH:MM libres para la fecha dada."""
    window = day_window(date_str)
    if not window:
        return []
    start, end = window
    taken = booked_times(date_str, exclude_booking_id=exclude_booking_id)
    today = datetime.now().strftime("%Y-%m-%d")
    now_hm = datetime.now().strftime("%H:%M")
    slots = []
    for hm in _iter_slots(start, end):
        if hm in taken:
            continue
        if date_str == today and hm <= now_hm:
            continue  # No ofrecer horarios ya pasados hoy.
        slots.append(hm)
    return slots


def is_slot_free(date_str: str, time_str: str, exclude_booking_id: int | None = None) -> bool:
    """True si el hueco date+time está libre."""
    return time_str in available_slots(date_str, exclude_booking_id=exclude_booking_id)
