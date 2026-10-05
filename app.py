# =============================================================================
# app.py — Factory Flask + SocketIO Beauty Nicaragua (versión profesional)
# =============================================================================

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import current_user, login_required, login_user, logout_user
from flask_socketio import emit, join_room

from availability import available_slots, is_slot_free
from chatbot import get_bot_response
from config import Config, ProductionConfig, validate_production
from extensions import csrf, db, limiter, login_manager, migrate, socketio
from models import Booking, ChatMessage, SalonInfo, Service, ServicePackage, User
from notifications import notify_booking_created, send_email, whatsapp_link
from routes_account import account_bp
from routes_admin import admin_bp
from seeds import seed_database
from validators import (
    validate_date,
    validate_email,
    validate_name,
    validate_password,
    validate_phone,
    validate_service_id,
    validate_time,
    validate_username,
)

BASE_DIR = Path(__file__).resolve().parent

# Sal para los tokens de restablecimiento de contraseña.
RESET_SALT = "beauty-password-reset-v1"
RESET_TOKEN_MAX_AGE = 3600  # 1 hora de validez del enlace.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("beauty")


def create_app(config_class=Config):
    """Crea la app Flask con seguridad, blueprints, BD y SocketIO."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Validación fail-fast: nunca arrancar en producción con secretos por defecto.
    if getattr(config_class, "IS_PRODUCTION", False):
        validate_production(app)

    # Pool acotado solo para Postgres (Supabase): conexiones estables con Supavisor.
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql"):
        app.config.setdefault(
            "SQLALCHEMY_ENGINE_OPTIONS",
            {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 5},
        )

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "instance").mkdir(exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    socketio.init_app(
        app,
        async_mode="threading",
        cors_allowed_origins=app.config.get("SOCKETIO_CORS_ORIGINS") or None,
    )

    # Detrás de Nginx/Railway/Render: IP y esquema reales para rate-limit y cookies seguras.
    if app.config.get("TRUST_PROXY_HEADERS"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    login_manager.login_view = "login"
    login_manager.login_message = "Inicia sesión para acceder."
    login_manager.login_message_category = "error"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()
        migrate_schema()
        seed_database(app)

    @app.after_request
    def set_security_headers(response):
        """Cabeceras HTTP de seguridad básicas."""
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.now(timezone.utc).year,
            "currency_symbol": app.config.get("CURRENCY_SYMBOL", "C$"),
            "currency_code": app.config.get("CURRENCY_CODE", "NIO"),
            "country_name": app.config.get("COUNTRY_NAME", "Nicaragua"),
            "whatsapp_url": whatsapp_link(),
            "csrf_enabled": app.config.get("WTF_CSRF_ENABLED", True),
        }

    @app.template_filter("nio")
    def format_nio(value):
        try:
            amount = float(value)
        except (TypeError, ValueError):
            return f"{app.config.get('CURRENCY_SYMBOL', 'C$')} —"
        return f"{app.config.get('CURRENCY_SYMBOL', 'C$')} {amount:,.0f}"

    register_error_handlers(app)
    register_routes(app)
    register_socket_events(app)

    app.register_blueprint(admin_bp)
    app.register_blueprint(account_bp)

    return app


def migrate_schema():
    """ALTER ligeros para BDs antiguas (complementa Flask-Migrate)."""
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if "users" in tables:
        cols = {c["name"] for c in inspector.get_columns("users")}
        if "is_admin" not in cols:
            db.session.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            db.session.commit()

    if "services" in tables:
        cols = {c["name"] for c in inspector.get_columns("services")}
        alters = []
        if "image_url" not in cols:
            alters.append("ALTER TABLE services ADD COLUMN image_url VARCHAR(500) DEFAULT ''")
        if "currency" not in cols:
            alters.append("ALTER TABLE services ADD COLUMN currency VARCHAR(3) DEFAULT 'NIO'")
        if "duration_minutes" not in cols:
            alters.append("ALTER TABLE services ADD COLUMN duration_minutes INTEGER DEFAULT 60")
        if "quote_only" not in cols:
            alters.append("ALTER TABLE services ADD COLUMN quote_only BOOLEAN DEFAULT 0")
        if "is_seed" not in cols:
            alters.append("ALTER TABLE services ADD COLUMN is_seed BOOLEAN DEFAULT 0")
        for sql in alters:
            db.session.execute(text(sql))
        if alters:
            db.session.commit()

    if "service_packages" in tables:
        cols = {c["name"] for c in inspector.get_columns("service_packages")}
        if "is_seed" not in cols:
            db.session.execute(text("ALTER TABLE service_packages ADD COLUMN is_seed BOOLEAN DEFAULT 0"))
            db.session.commit()

    if "bookings" in tables:
        cols = {c["name"] for c in inspector.get_columns("bookings")}
        alters = []
        if "user_id" not in cols:
            alters.append("ALTER TABLE bookings ADD COLUMN user_id INTEGER")
        if "preferred_time" not in cols:
            alters.append("ALTER TABLE bookings ADD COLUMN preferred_time VARCHAR(10) DEFAULT '09:00'")
        if "package_id" not in cols:
            alters.append("ALTER TABLE bookings ADD COLUMN package_id INTEGER")
        if "payment_status" not in cols:
            alters.append("ALTER TABLE bookings ADD COLUMN payment_status VARCHAR(30) DEFAULT 'unpaid'")
        if "payment_proof" not in cols:
            alters.append("ALTER TABLE bookings ADD COLUMN payment_proof VARCHAR(255) DEFAULT ''")
        if "deposit_amount" not in cols:
            alters.append("ALTER TABLE bookings ADD COLUMN deposit_amount FLOAT DEFAULT 0")
        if "admin_notes" not in cols:
            alters.append("ALTER TABLE bookings ADD COLUMN admin_notes TEXT DEFAULT ''")
        if "updated_at" not in cols:
            alters.append("ALTER TABLE bookings ADD COLUMN updated_at DATETIME")
        for sql in alters:
            db.session.execute(text(sql))
        if alters:
            db.session.commit()

    _ensure_unique_slot_index()


def _ensure_unique_slot_index():
    """Índice único parcial anti doble-reserva (SQLite y Postgres lo soportan).

    Si la BD ya contiene citas activas duplicadas, la creación falla: se
    registra advertencia sin romper el arranque (hay que depurar los duplicados).
    """
    try:
        db.session.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_bookings_active_slot "
                "ON bookings (preferred_date, preferred_time) "
                "WHERE status IN ('pending','confirmed','reschedule')"
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.warning(
            "No se pudo crear uq_bookings_active_slot (¿citas activas duplicadas?). "
            "Deduplica bookings activos por fecha+hora y reinicia."
        )


def get_salon_info():
    return {row.key: row.value for row in SalonInfo.query.all()}


def get_chat_session_id():
    if "chat_session_id" not in session:
        session["chat_session_id"] = uuid.uuid4().hex
    return session["chat_session_id"]


def safe_next_path(raw_path: str | None) -> str:
    """Evita redirects abiertos hacia sitios externos."""
    if not raw_path:
        return "/"
    parsed = urlparse(raw_path)
    if parsed.scheme or parsed.netloc:
        return "/"
    if raw_path.startswith("/"):
        return raw_path
    return "/"


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("Error 500")
        return render_template("errors/500.html"), 500


def register_routes(app):
    @app.route("/")
    def index():
        services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
        packages = ServicePackage.query.filter_by(is_active=True).order_by(ServicePackage.sort_order).all()
        info = get_salon_info()
        return render_template("index.html", services=services, packages=packages, info=info)

    @app.route("/api/slots")
    def api_slots():
        """JSON de horarios libres para una fecha (agenda real)."""
        date_str = request.args.get("date", "").strip()
        if validate_date(date_str):
            return jsonify({"ok": False, "slots": [], "error": "Fecha inválida"}), 400
        slots = available_slots(date_str)
        return jsonify({"ok": True, "slots": slots, "closed": len(slots) == 0})

    @app.route("/registro", methods=["GET", "POST"])
    @limiter.limit(Config.LOGIN_RATE_LIMIT)
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        next_page = safe_next_path(request.args.get("next") or request.form.get("next"))

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")

            errors = [
                e
                for e in (
                    validate_name(full_name),
                    validate_username(username),
                    validate_email(email),
                    validate_phone(phone),
                    validate_password(password, confirm),
                )
                if e
            ]
            if User.query.filter_by(username=username).first():
                errors.append("Ese nombre de usuario ya está en uso.")
            if User.query.filter_by(email=email).first():
                errors.append("Ese email ya está registrado.")

            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("auth/register.html", form_data=request.form, next_page=next_page)

            user = User(full_name=full_name, username=username, email=email, phone=phone)
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Ese usuario o email acaba de registrarse. Probá con otro.", "error")
                return render_template("auth/register.html", form_data=request.form, next_page=next_page)
            login_user(user)
            flash(f"¡Bienvenida, {full_name}! Tu cuenta ha sido creada.", "success")
            return redirect(next_page)

        return render_template("auth/register.html", form_data={}, next_page=next_page)

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit(Config.LOGIN_RATE_LIMIT)
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        next_page = safe_next_path(request.args.get("next") or request.form.get("next"))

        if request.method == "POST":
            identifier = request.form.get("identifier", "").strip()
            password = request.form.get("password", "")
            if not identifier or not password:
                flash("Completa todos los campos.", "error")
                return render_template("auth/login.html", next_page=next_page)

            user = User.query.filter(
                (User.email == identifier) | (User.username == identifier)
            ).first()
            if user and user.check_password(password):
                login_user(user, remember=request.form.get("remember") == "on")
                flash(f"¡Hola de nuevo, {user.full_name}!", "success")
                if user.is_admin and not next_page:
                    return redirect(url_for("admin.dashboard"))
                return redirect(next_page or url_for("index"))

            flash("Usuario o contraseña incorrectos.", "error")

        return render_template("auth/login.html", next_page=next_page)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Has cerrado sesión correctamente.", "success")
        return redirect(url_for("index"))

    # --- Restablecimiento de contraseña --------------------------------------

    def _reset_serializer() -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt=RESET_SALT)

    @app.route("/recuperar", methods=["GET", "POST"])
    @limiter.limit("5 per minute")
    def recuperar():
        """Solicitud de restablecimiento (sin revelar si el email existe)."""
        if request.method == "POST":
            identifier = request.form.get("identifier", "").strip()
            user = User.query.filter(
                (User.email == identifier) | (User.username == identifier)
            ).first()
            if user:
                token = _reset_serializer().dumps(user.id)
                reset_url = url_for("restablecer", token=token, _external=True)
                body = (
                    f"Hola {user.full_name},\n\n"
                    f"Recibimos una solicitud para restablecer tu contraseña en Beauty Nicaragua.\n"
                    f"Abre este enlace (vence en 1 hora):\n{reset_url}\n\n"
                    f"Si no fuiste tú, ignora este mensaje y tu contraseña no cambiará.\n"
                    f"— Beauty Nicaragua (Managua)"
                )
                send_email(user.email, "Restablece tu contraseña — Beauty Nicaragua", body)
            flash(
                "Si la cuenta existe, te enviamos un email con instrucciones.",
                "info",
            )
            return redirect(url_for("login"))
        return render_template("auth/recuperar.html")

    @app.route("/restablecer/<token>", methods=["GET", "POST"])
    @limiter.limit("10 per hour")
    def restablecer(token):
        try:
            user_id = _reset_serializer().loads(token, max_age=RESET_TOKEN_MAX_AGE)
        except SignatureExpired:
            flash("El enlace expiró. Solicita uno nuevo.", "error")
            return redirect(url_for("recuperar"))
        except BadSignature:
            flash("El enlace no es válido.", "error")
            return redirect(url_for("recuperar"))

        user = db.session.get(User, int(user_id))
        if not user:
            flash("Cuenta no encontrada.", "error")
            return redirect(url_for("recuperar"))

        if request.method == "POST":
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            error = validate_password(password, confirm)
            if error:
                flash(error, "error")
                return render_template("auth/restablecer.html", token=token)
            user.set_password(password)
            db.session.commit()
            flash("Contraseña actualizada. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("login"))

        return render_template("auth/restablecer.html", token=token)

    @app.route("/reservar", methods=["POST"])
    @login_required
    @limiter.limit(Config.BOOKING_RATE_LIMIT)
    def reservar():
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        service_id = request.form.get("service_id", type=int)
        package_id = request.form.get("package_id", type=int)
        preferred_date = request.form.get("preferred_date", "").strip()
        preferred_time = request.form.get("preferred_time", "").strip()
        message = request.form.get("message", "").strip()
        want_deposit = request.form.get("want_deposit") == "on"

        service = db.session.get(Service, service_id) if service_id else None
        package = db.session.get(ServicePackage, package_id) if package_id else None

        errors = [
            e
            for e in (
                validate_name(full_name),
                validate_email(email),
                validate_phone(phone),
                validate_date(preferred_date),
                validate_time(preferred_time),
            )
            if e
        ]
        if not service and not package:
            errors.append("Selecciona un servicio o pack.")
        if service and validate_service_id(service_id, service):
            errors.append(validate_service_id(service_id, service))
        if preferred_date and preferred_time and not is_slot_free(preferred_date, preferred_time):
            errors.append("Ese horario ya está ocupado. Elegí otro.")

        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("index", _anchor="reservar"))

        price = package.price if package else service.price
        deposit = round(price * (app.config["DEPOSIT_PERCENT"] / 100.0), 0) if want_deposit else 0.0

        booking = Booking(
            user_id=current_user.id,
            full_name=full_name,
            email=email,
            phone=phone,
            service_id=service.id if service else None,
            package_id=package.id if package else None,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            message=message,
            status="pending",
            payment_status="unpaid",
            deposit_amount=deposit,
        )
        db.session.add(booking)
        try:
            db.session.commit()
        except IntegrityError:
            # Índice único parcial uq_bookings_active_slot: alguien reservó el
            # hueco entre el chequeo y el commit (race condition).
            db.session.rollback()
            logger.warning("Colisión de reserva detectada: %s %s", preferred_date, preferred_time)
            flash("Ese horario acaba de ser reservado por otra persona. Elegí otro, por favor.", "error")
            return redirect(url_for("index", _anchor="reservar"))

        try:
            notify_booking_created(booking)
        except Exception:
            logger.exception("Notificación falló (la cita sí se guardó)")

        flash(
            f"¡Gracias, {full_name}! Cita solicitada para {preferred_date} {preferred_time}. "
            f"Revisá tu email / Mi cuenta. WhatsApp: {app.config['WHATSAPP_NUMBER']}.",
            "success",
        )
        return redirect(url_for("account.dashboard"))

    @app.route("/privacidad")
    def privacy():
        return render_template("legal/privacy.html")

    @app.route("/terminos")
    def terms():
        return render_template("legal/terms.html")


def register_socket_events(app):
    @socketio.on("connect")
    def handle_connect():
        if not current_user.is_authenticated:
            emit("auth_required", {"message": "Debés iniciar sesión para chatear con Bella."})
            return False
        sid = get_chat_session_id()
        join_room(sid)
        emit("connected", {"session_id": sid, "user": current_user.full_name.split()[0]})

    @socketio.on("send_message")
    def handle_message(data):
        with app.app_context():
            if not current_user.is_authenticated:
                emit("auth_required", {"message": "Sesión expirada. Iniciá sesión para continuar."})
                return

            content = (data or {}).get("message", "").strip()
            if not content or len(content) > 500:
                emit("bot_message", {"message": "Mensaje no válido. Máximo 500 caracteres."})
                return

            sid = get_chat_session_id()
            user_msg = ChatMessage(
                user_id=current_user.id, session_id=sid, sender="user", content=content
            )
            db.session.add(user_msg)
            db.session.commit()
            emit("user_message", {"message": content})

            services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
            info = get_salon_info()
            bot_reply = get_bot_response(content, services, info)

            bot_msg = ChatMessage(
                user_id=current_user.id, session_id=sid, sender="bot", content=bot_reply
            )
            db.session.add(bot_msg)
            db.session.commit()
            emit("bot_message", {"message": bot_reply})


# Selección de config por entorno: FLASK_ENV=production → ProductionConfig.
app = create_app(ProductionConfig if os.environ.get("FLASK_ENV") == "production" else Config)


if __name__ == "__main__":
    # Servidor de desarrollo SOLO (gunicorn sirve producción; ver Procfile).
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
