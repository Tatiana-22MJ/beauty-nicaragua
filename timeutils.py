# =============================================================================
# timeutils.py — Tiempo canónico del negocio (America/Managua)
# =============================================================================

from datetime import datetime
from zoneinfo import ZoneInfo

# El salón opera en Nicaragua. Toda la agenda (fechas mínimas, slots pasados,
# validaciones) se calcula en la zona del negocio, nunca en la hora del
# servidor (que puede ser UTC en producción).
NICARAGUA_TZ = ZoneInfo("America/Managua")


def now_ni() -> datetime:
    """datetime "aware" en la zona America/Managua."""
    return datetime.now(NICARAGUA_TZ)


def today_ni():
    """Fecha de hoy en Nicaragua (independiente de la hora del servidor)."""
    return now_ni().date()
