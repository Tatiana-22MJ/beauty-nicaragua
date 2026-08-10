# =============================================================================
# models.py — Modelos ORM Beauty Nicaragua (operación profesional)
# =============================================================================

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    """Cuenta de clienta o administradora."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), default="")
    is_admin = db.Column(db.Boolean, default=False, nullable=False)  # Acceso al panel /admin.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    bookings = db.relationship("Booking", backref="user", lazy=True)
    chat_messages = db.relationship("ChatMessage", backref="user", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} admin={self.is_admin}>"


class Service(db.Model):
    """Tratamiento individual con precio en NIO."""

    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default="NIO")
    duration_minutes = db.Column(db.Integer, default=60)  # Duración para slots de agenda.
    icon = db.Column(db.String(16), default="✨")
    image_url = db.Column(db.String(500), default="")
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    quote_only = db.Column(db.Boolean, default=False)  # True = “consultar precio” (ej. láser zonas).

    def __repr__(self):
        return f"<Service {self.name}>"


class ServicePackage(db.Model):
    """Pack / combo estilo mercado NI (spa + manicura + facial, etc.)."""

    __tablename__ = "service_packages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    includes = db.Column(db.Text, default="")  # Lista legible de lo incluido.
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default="NIO")
    image_url = db.Column(db.String(500), default="")
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<ServicePackage {self.name}>"


class Booking(db.Model):
    """Cita con horario, estado operativo y pago por transferencia."""

    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=True)
    package_id = db.Column(db.Integer, db.ForeignKey("service_packages.id"), nullable=True)
    preferred_date = db.Column(db.String(20), nullable=False)  # YYYY-MM-DD
    preferred_time = db.Column(db.String(10), nullable=False, default="09:00")  # HH:MM
    message = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="pending")  # pending|confirmed|cancelled|completed|reschedule
    payment_status = db.Column(db.String(30), default="unpaid")  # unpaid|pending_transfer|paid
    payment_proof = db.Column(db.String(255), default="")  # Nombre de archivo en uploads/
    deposit_amount = db.Column(db.Float, default=0.0)  # Anticipo sugerido en C$.
    admin_notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    service = db.relationship("Service", backref=db.backref("bookings", lazy=True))
    package = db.relationship("ServicePackage", backref=db.backref("bookings", lazy=True))

    @property
    def title(self) -> str:
        if self.service:
            return self.service.name
        if self.package:
            return self.package.name
        return "Cita"

    def __repr__(self):
        return f"<Booking {self.id} {self.status} {self.preferred_date} {self.preferred_time}>"


class ChatMessage(db.Model):
    """Mensaje de chat persistido."""

    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<ChatMessage {self.sender}>"


class SalonInfo(db.Model):
    """Config key/value del salón."""

    __tablename__ = "salon_info"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<SalonInfo {self.key}>"


class AuditLog(db.Model):
    """Registro simple de acciones admin (auditoría ligera)."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(120), nullable=False)
    detail = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
