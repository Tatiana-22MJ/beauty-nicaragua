# =============================================================================
# availability.py — Generación y validación de horarios disponibles
# =============================================================================

from datetime import datetime, time, timedelta

from models import Booking
from timeutils import now_ni, today_ni

# Horarios operativos Managua (alineados a SalonInfo).
WEEKDAY_START = time(8, 0)
WEEKDAY_END = time(18, 0)
SATURDAY_START = time(8, 0)
SATURDAY_END = time(14, 0)
SLOT_MINUTES = 60  # Granularidad de la agenda.
DEFAULT_DURATION = 60  # Duración por defecto (packs / sin servicio asociado).
ACTIVE_STATUSES = ("pending", "confirmed", "reschedule")  # Ocupan el hueco.


def _iter_slots(start: time, end: time, step_minutes: int = SLOT_MINUTES):
    """Genera strings HH:MM desde start inclusive hasta end exclusive."""
    cursor = datetime.combine(datetime.today().date(), start)
    limit = datetime.combine(datetime.today().date(), end)
    while cursor < limit:
        yield cursor.strftime("%H:%M")
        cursor += timedelta(minutes=step_minutes)


def to_minutes(hm: str) -> int | None:
    """Convierte "HH:MM" a minutos desde medianoche; None si no es válido."""
    try:
        hours, minutes = (int(part) for part in (hm or "").split(":", 1))
    except (TypeError, ValueError):
        return None
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        return None
    return hours * 60 + minutes


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


def duration_for(service=None, package=None) -> int:
    """Duración a bloquear: la del servicio, la del pack, o 60 min."""
    if service is not None and getattr(service, "duration_minutes", None):
        return int(service.duration_minutes)
    if package is not None and getattr(package, "duration_minutes", None):
        return int(package.duration_minutes)
    return DEFAULT_DURATION


def booking_duration_minutes(booking) -> int:
    """Duración real de una cita: la del servicio (o pack); 60 min por defecto."""
    return duration_for(
        getattr(booking, "service", None),
        getattr(booking, "package", None),
    )


def booked_intervals(date_str: str, exclude_booking_id: int | None = None) -> list[tuple[int, int]]:
    """Intervalos ocupados (inicio, fin) en minutos para la fecha dada."""
    query = Booking.query.filter(
        Booking.preferred_date == date_str,
        Booking.status.in_(ACTIVE_STATUSES),
    )
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)

    intervals: list[tuple[int, int]] = []
    for booking in query.all():
        start = to_minutes(booking.preferred_time)
        if start is None:
            continue
        intervals.append((start, start + booking_duration_minutes(booking)))
    return intervals


def booked_times(date_str: str, exclude_booking_id: int | None = None) -> set[str]:
    """Horarios ya tomados en una fecha (pending/confirmed/reschedule)."""
    query = Booking.query.filter(
        Booking.preferred_date == date_str,
        Booking.status.in_(ACTIVE_STATUSES),
    )
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    return {b.preferred_time for b in query.all() if b.preferred_time}


def _overlaps(intervals: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(start < busy_end and busy_start < end for busy_start, busy_end in intervals)


def available_slots(
    date_str: str,
    duration_minutes: int = DEFAULT_DURATION,
    exclude_booking_id: int | None = None,
) -> list[str]:
    """HH:MM libres donde el servicio cabe completo antes del cierre.

    Un hueco se considera ocupado si el intervalo [inicio, inicio+duración)
    se solapa con cualquier cita activa existente (con su propia duración),
    de modo que un balayage de 120 min bloquea dos huecos y un servicio de
    45 min no inhabilita la hora siguiente.
    """
    window = day_window(date_str)
    if not window:
        return []
    start, end = window
    end_minutes = to_minutes(end.strftime("%H:%M"))
    duration = max(int(duration_minutes or DEFAULT_DURATION), 1)
    intervals = booked_intervals(date_str, exclude_booking_id=exclude_booking_id)
    today = today_ni().strftime("%Y-%m-%d")
    now_hm = now_ni().strftime("%H:%M")

    slots = []
    for hm in _iter_slots(start, end):
        slot_start = to_minutes(hm)
        if slot_start is None:
            continue
        if slot_start + duration > end_minutes:
            continue  # El servicio no cabe antes del cierre.
        if _overlaps(intervals, slot_start, slot_start + duration):
            continue
        if date_str == today and hm <= now_hm:
            continue  # No ofrecer horarios ya pasados hoy.
        slots.append(hm)
    return slots


def is_slot_free(
    date_str: str,
    time_str: str,
    duration_minutes: int = DEFAULT_DURATION,
    exclude_booking_id: int | None = None,
) -> bool:
    """True si date+time está libre y el servicio de `duration_minutes` cabe."""
    return time_str in available_slots(
        date_str,
        duration_minutes=duration_minutes,
        exclude_booking_id=exclude_booking_id,
    )
