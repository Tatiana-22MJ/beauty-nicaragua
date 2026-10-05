# =============================================================================
# validators.py — Validación server-side
# =============================================================================

import re
from datetime import datetime

from timeutils import today_ni

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
    if day < today_ni():
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


# --- Parsers defensivos (inputs de formularios admin / públicos) --------------


def parse_float(raw, field: str = "valor", minimum: float = 0.0) -> tuple[float | None, str | None]:
    """Convierte un string de formulario a float; devuelve (valor, error)."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, f"El campo {field} debe ser un número válido."
    if value < minimum:
        return None, f"El campo {field} no puede ser menor que {minimum}."
    return value, None


def parse_int(raw, field: str = "valor", minimum: int = 0) -> tuple[int | None, str | None]:
    """Convierte un string de formulario a int; devuelve (valor, error)."""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None, f"El campo {field} debe ser un número entero válido."
    if value < minimum:
        return None, f"El campo {field} no puede ser menor que {minimum}."
    return value, None


# --- Validación de archivos por firma (magic bytes) ---------------------------
# La extensión se puede falsificar; la firma del contenido no.

_FILE_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"%PDF-", "pdf"),
)  # WEBP se valida aparte (RIFF....WEBP).


def validate_file_signature(stream, filename: str) -> str | None:
    """Verifica que el archivo sea realmente PNG/JPG/WEBP/PDF por su contenido.

    ``stream`` debe ser un file-like legible (rebobina con seek(0) al terminar).
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in {"png", "jpg", "jpeg", "webp", "pdf"}:
        return "Formato no permitido. Usá PNG, JPG, WEBP o PDF."

    head = stream.read(16)
    stream.seek(0)
    if not head:
        return "El archivo está vacío."

    for signature, _kind in _FILE_SIGNATURES:
        if head.startswith(signature):
            return None
    if head[0:4] == b"RIFF" and head[8:12] == b"WEBP":
        return None
    return "El archivo no es una imagen o PDF válido."
