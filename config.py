# =============================================================================
# config.py — Configuración Beauty Nicaragua (dev + producción)
# =============================================================================

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Configuración base."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "beauty-dev-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'beauty.db'}",
    )
    # Heroku/Railway a veces usan postgres:// — SQLAlchemy espera postgresql://
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Moneda / país
    CURRENCY_CODE = "NIO"
    CURRENCY_SYMBOL = "C$"
    COUNTRY_CODE = "NI"
    COUNTRY_NAME = "Nicaragua"
    DEFAULT_LOCALE = "es_NI"
    TIMEZONE = "America/Managua"

    # Seguridad de cookies de sesión
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Tokens CSRF no expiran en la sesión (UX formularios largos).

    # Uploads (comprobantes de transferencia)
    UPLOAD_FOLDER = str(BASE_DIR / "instance" / "uploads")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB
    ALLOWED_PROOF_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

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

    # Rate limits específicos (strings flask-limiter)
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    LOGIN_RATE_LIMIT = "10 per minute"
    CHAT_RATE_LIMIT = "30 per minute"
    BOOKING_RATE_LIMIT = "10 per minute"

    # Admin seed (solo si no existe)
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@beauty-nicaragua.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin123!")


class ProductionConfig(Config):
    """Overrides seguros para producción."""

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True
