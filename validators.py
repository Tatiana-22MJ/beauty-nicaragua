# =============================================================================
# validators.py — Validación server-side
# =============================================================================

import re
from datetime import datetime

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(r"^\+?[\d\s\-()]{8,20}$")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def validate_name(value: str) -> str | None:
    value = (value or "").strip()
    if len(value) < 2:
        return "El nombre debe tener al menos 2 caracteres."
    if len(value) > 120:
        return "El nombre es demasiado largo."
    return None


def validate_email(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return "El email es obligatorio."
    if not EMAIL_RE.match(value):
        return "Introduce un email válido."
    return None


def validate_phone(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return "El teléfono es obligatorio."
    if not PHONE_RE.match(value):
        return "Introduce un teléfono válido (ej. +505 8877 2117)."
    return None


def validate_username(value: str) -> str | None:
    value = (value or "").strip()
    if not USERNAME_RE.match(value):
        return "Usuario: 3-30 caracteres, solo letras, números y _."
    return None


def validate_password(value: str, confirm: str = "") -> str | None:
    if not value or len(value) < 8:
        return "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        return "La contraseña debe incluir letras y números."
    if confirm and value != confirm:
        return "Las contraseñas no coinciden."
    return None


def validate_date(value: str) -> str | None:
    if not value:
        return "Indica una fecha preferida."
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return "Fecha no válida."
    if day < datetime.now().date():
        return "La fecha no puede ser pasada."
    return None


def validate_time(value: str) -> str | None:
    if not value or not TIME_RE.match(value):
        return "Selecciona un horario disponible."
    return None


def validate_service_id(value, service_exists) -> str | None:
    if not value or not service_exists:
        return "Selecciona un servicio válido."
    return None
