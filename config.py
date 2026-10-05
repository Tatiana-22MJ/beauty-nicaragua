# =============================================================================
# config.py — Configuración Beauty Nicaragua (dev + producción + Supabase)
# =============================================================================

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Carga .env ANTES de leer os.environ (el archivo nunca se committe).
load_dotenv(BASE_DIR / ".env")

# --- Valores por defecto inseguros (detectados en producción por validate_production) ---
_INSECURE_SECRET_KEY = "beauty-dev-key-change-in-production"
_INSECURE_ADMIN_PASSWORD = "Admin123!"

# --- Normalización de la URI de base de datos ---------------------------------
# Soporta: SQLite local (dev) y Postgres/Supabase (producción) con psycopg3.
#   postgres://        → postgresql+psycopg://   (Heroku/Railway legacy + driver)
#   postgresql://      → postgresql+psycopg://   (cadena del pooler de Supabase)
#   postgresql+psycopg:// ... postgresql+psycopg2:// → se respetan tal cual.
_raw_uri = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'instance' / 'beauty.db'}",
)
if _raw_uri.startswith("postgres://"):
    _raw_uri = _raw_uri.replace("postgres://", "postgresql://", 1)
if _raw_uri.startswith("postgresql://"):
    _raw_uri = _raw_uri.replace("postgresql://", "postgresql+psycopg://", 1)


class Config:
    """Configuración base (desarrollo)."""

    # Un env var definido pero vacío se trata como no definido (cae al default
    # inseguro, que validate_production bloquea en producción).
    SECRET_KEY = os.environ.get("SECRET_KEY", "").strip() or _INSECURE_SECRET_KEY
    SQLALCHEMY_DATABASE_URI = _raw_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # En Postgres (Supabase) se activan pool_pre_ping + pool acotado en create_app.

    IS_PRODUCTION = False  # True en ProductionConfig → activa validaciones estrictas.

    # Moneda / país
    CURRENCY_CODE = "NIO"
    CURRENCY_SYMBOL = "C$"
    COUNTRY_CODE = "NI"
    COUNTRY_NAME = "Nicaragua"
    DEFAULT_LOCALE = "es_NI"
    TIMEZONE = "America/Managua"

    # Seguridad de cookies y sesiones
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Tokens CSRF no expiran en la sesión (UX formularios largos).

    # Proxy inverso (Nginx / Railway / Render): marcar TRUST_PROXY_HEADERS=1
    # para que rate-limiting e IP real funcionen detrás del proxy.
    TRUST_PROXY_HEADERS = os.environ.get("TRUST_PROXY_HEADERS", "0") == "1"

    # WebSocket (chat Bella): same-origin por defecto. Para dominios extra,
    # lista separada por comas en SOCKETIO_CORS_ORIGINS.
    SOCKETIO_CORS_ORIGINS = [
        origin.strip() for origin in os.environ.get("SOCKETIO_CORS_ORIGINS", "").split(",") if origin.strip()
    ]

    # Uploads (comprobantes de transferencia)
    UPLOAD_FOLDER = str(BASE_DIR / "instance" / "uploads")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB
    ALLOWED_PROOF_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

    # --- Supabase ------------------------------------------------------------
    # Expuestas como atributos de Config (verificar existencia, jamás imprimir):
    #   SUPABASE_URL             → https://<ref>.supabase.co
    #   SUPABASE_PUBLISHABLE_KEY → clave pública (frontend); legacy: SUPABASE_ANON_KEY
    #   SUPABASE_SECRET_KEY      → clave secreta del servidor; legacy: SUPABASE_SERVICE_ROLE_KEY
    #   DATABASE_URL             → cadena del pooler (puerto 5432) o SQLite local
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
    SUPABASE_PUBLISHABLE_KEY = (
        os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()  # formato nuevo
        or os.environ.get("SUPABASE_ANON_KEY", "").strip()  # legacy
    )
    SUPABASE_SECRET_KEY = (
        os.environ.get("SUPABASE_SECRET_KEY", "").strip()  # formato nuevo
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()  # legacy
    )
    # Alias para código interno existente (supabase_storage.py).
    SUPABASE_SERVICE_ROLE_KEY = SUPABASE_SECRET_KEY
    SUPABASE_BUCKET_PROOFS = os.environ.get("SUPABASE_BUCKET_PROOFS", "payment-proofs")

    DATABASE_URL = _raw_uri  # Alias legible de SQLALCHEMY_DATABASE_URI.

    # --- Observabilidad --------------------------------------------------------
    # SENTRY_DSN vacío = sin Sentry (dev). En producción: pega el DSN de tu
    # proyecto Sentry (free tier) para capturar 500s y excepciones.
    SENTRY_DSN = os.environ.get("SENTRY_DSN", "").strip()
    SENTRY_TRACES_SAMPLE_RATE = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    # LOG_FORMAT=json → logs en JSON por línea (ingesta en Railway / Sentry).

    # WhatsApp Business / contacto
    WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "50576721749")  # sin +
    WHATSAPP_DEFAULT_MSG = os.environ.get(
        "WHATSAPP_DEFAULT_MSG",
        "Hola Beauty Nicaragua, quiero consultar una cita.",
    )

    # Email (si no hay SMTP, se registra en logs)
    MAIL_ENABLED = (os.environ.get("MAIL_ENABLED", "0") == "1") or bool(
        os.environ.get("MAIL_USERNAME", "") and os.environ.get("MAIL_PASSWORD", "")
    )
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "1") == "1"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "Beauty Nicaragua <info@beauty-nicaragua.com>")
    ADMIN_NOTIFY_EMAIL = os.environ.get("ADMIN_NOTIFY_EMAIL", "admin@beauty-nicaragua.com")

    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "")

    # Anticipo sugerido (% del precio) para transferencias
    DEPOSIT_PERCENT = float(os.environ.get("DEPOSIT_PERCENT", "30"))

    # Cuenta bancaria demo para transferencias (mostrar en UI)
    BANK_NAME = os.environ.get("BANK_NAME", "BAC Credomatic")
    BANK_ACCOUNT = os.environ.get("BANK_ACCOUNT", "XXXX-XXXX-XXXX-1234")
    BANK_HOLDER = os.environ.get("BANK_HOLDER", "Beauty Nicaragua S.A.")

    # Datos de pago adicionales (opcionales): teléfono, link y QR
    PAYMENT_PHONE = os.environ.get("PAYMENT_PHONE", "").strip()
    PAYMENT_REFERENCE = os.environ.get("PAYMENT_REFERENCE", "").strip()
    PAYMENT_LINK = os.environ.get("PAYMENT_LINK", "").strip()
    PAYMENT_QR_URL = os.environ.get("PAYMENT_QR_URL", "").strip()

    # Rate limits (flask-limiter). En producción con >1 worker usar Redis:
    #   RATELIMIT_STORAGE_URI=redis://localhost:6379/0
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    LOGIN_RATE_LIMIT = "10 per minute"
    CHAT_RATE_LIMIT = "30 per minute"
    BOOKING_RATE_LIMIT = "10 per minute"

    # Admin seed (solo si no existe)
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@beauty-nicaragua.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "").strip() or _INSECURE_ADMIN_PASSWORD


class ProductionConfig(Config):
    """Overrides seguros para producción."""

    IS_PRODUCTION = True
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


def validate_production(app) -> None:
    """Fail-fast: impide arrancar en producción con credenciales inseguras.

    Evita el peor escenario: SECRET_KEY conocida públicamente o vacía (sesiones
    falsificables) o admin con contraseña por defecto/ vacía.
    """
    problems: list[str] = []
    secret_key = app.config.get("SECRET_KEY") or ""
    if not secret_key.strip() or secret_key == _INSECURE_SECRET_KEY:
        problems.append(
            "SECRET_KEY está vacía o sigue en su valor por defecto. "
            "Define la variable de entorno SECRET_KEY (python -c \"import secrets; print(secrets.token_hex(32))\")."
        )
    admin_password = app.config.get("ADMIN_PASSWORD") or ""
    if not admin_password.strip() or admin_password == _INSECURE_ADMIN_PASSWORD:
        problems.append("ADMIN_PASSWORD está vacía o sigue en su valor por defecto. Define una contraseña fuerte.")
    if not app.config.get("SESSION_COOKIE_SECURE"):
        problems.append("SESSION_COOKIE_SECURE debe ser 1 (HTTPS obligatorio) en producción.")
    if problems:
        raise RuntimeError(
            "Configuración de producción inválida:\n- " + "\n- ".join(problems)
        )
