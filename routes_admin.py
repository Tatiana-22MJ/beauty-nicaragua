# =============================================================================
# routes_admin.py — Panel administrativo (servicios, citas, chats, packs)
# =============================================================================

from functools import wraps
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from extensions import db
from models import AuditLog, Booking, ChatMessage, Service, ServicePackage, User
from notifications import notify_booking_status
from supabase_storage import proof_signed_url
from validators import parse_float, parse_int, validate_name

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    """Decorator: exige login + is_admin."""

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def _audit(action: str, detail: str = "") -> None:
    db.session.add(
        AuditLog(user_id=current_user.id if current_user.is_authenticated else None, action=action, detail=detail)
    )


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "bookings_pending": Booking.query.filter_by(status="pending").count(),
        "bookings_confirmed": Booking.query.filter_by(status="confirmed").count(),
        "services": Service.query.count(),
        "users": User.query.count(),
        "messages": ChatMessage.query.count(),
        "payments_pending": Booking.query.filter_by(payment_status="pending_transfer").count(),
    }
    recent = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


def _parse_service_form() -> tuple[dict, list[str]]:
    """Parsea y valida el formulario de servicios sin permitir 500s."""
    fields: dict = {}
    errors: list[str] = []

    name = request.form.get("name", "").strip()
    error = validate_name(name)
    if error:
        errors.append(error)
    fields["name"] = name

    price, error = parse_float(request.form.get("price"), "precio", minimum=0)
    if error:
        errors.append(error)
    fields["price"] = price

    duration, error = parse_int(request.form.get("duration_minutes"), "duración (min)", minimum=15)
    if error:
        errors.append(error)
    fields["duration_minutes"] = duration

    sort_order, error = parse_int(request.form.get("sort_order"), "orden", minimum=0)
    if error:
        errors.append(error)
    fields["sort_order"] = sort_order

    fields["description"] = request.form.get("description", "").strip()
    fields["icon"] = request.form.get("icon", "✨").strip() or "✨"
    fields["image_url"] = request.form.get("image_url", "").strip()
    fields["quote_only"] = request.form.get("quote_only") == "on"
    return fields, errors


@admin_bp.route("/servicios", methods=["GET", "POST"])
@admin_required
def services():
    if request.method == "POST":
        action = request.form.get("action")
        fields, errors = _parse_service_form()
        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("admin.services"))

        if action == "create":
            service = Service(
                name=fields["name"],
                description=fields["description"],
                price=fields["price"],
                currency="NIO",
                duration_minutes=fields["duration_minutes"],
                icon=fields["icon"],
                image_url=fields["image_url"],
                sort_order=fields["sort_order"],
                quote_only=fields["quote_only"],
                is_active=True,
                is_seed=False,  # Creado por admin: el seed nunca lo borra.
            )
            db.session.add(service)
            _audit("service_create", service.name)
            db.session.commit()
            flash("Servicio creado.", "success")
        elif action == "update":
            service = db.session.get(Service, int(request.form.get("service_id", 0) or 0))
            if service:
                service.name = fields["name"] or service.name
                service.description = fields["description"] or service.description
                service.price = fields["price"] if fields["price"] is not None else service.price
                service.duration_minutes = fields["duration_minutes"] or service.duration_minutes
                service.icon = fields["icon"]
                service.image_url = fields["image_url"]
                service.sort_order = fields["sort_order"] if fields["sort_order"] is not None else service.sort_order
                service.quote_only = fields["quote_only"]
                service.is_active = request.form.get("is_active") == "on"
                _audit("service_update", f"{service.id}:{service.name}")
                db.session.commit()
                flash("Servicio actualizado.", "success")
        return redirect(url_for("admin.services"))

    items = Service.query.order_by(Service.sort_order).all()
    return render_template("admin/services.html", services=items)


@admin_bp.route("/packs", methods=["GET", "POST"])
@admin_required
def packages():
    if request.method == "POST":
        action = request.form.get("action")

        name = request.form.get("name", "").strip()
        price, price_error = parse_float(request.form.get("price"), "precio", minimum=0)
        sort_order, sort_error = parse_int(request.form.get("sort_order"), "orden", minimum=0)
        errors = [e for e in (validate_name(name), price_error, sort_error) if e]
        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("admin.packages"))

        if action == "create":
            pack = ServicePackage(
                name=name,
                description=request.form.get("description", "").strip(),
                includes=request.form.get("includes", "").strip(),
                price=price,
                currency="NIO",
                image_url=request.form.get("image_url", "").strip(),
                sort_order=sort_order,
                is_active=True,
                is_seed=False,  # Creado por admin: el seed nunca lo borra.
            )
            db.session.add(pack)
            _audit("package_create", pack.name)
            db.session.commit()
            flash("Pack creado.", "success")
        elif action == "update":
            pack = db.session.get(ServicePackage, int(request.form.get("package_id", 0) or 0))
            if pack:
                pack.name = name or pack.name
                pack.description = request.form.get("description", pack.description).strip()
                pack.includes = request.form.get("includes", pack.includes).strip()
                pack.price = price if price is not None else pack.price
                pack.image_url = request.form.get("image_url", pack.image_url).strip()
                pack.sort_order = sort_order if sort_order is not None else pack.sort_order
                pack.is_active = request.form.get("is_active") == "on"
                _audit("package_update", f"{pack.id}:{pack.name}")
                db.session.commit()
                flash("Pack actualizado.", "success")
        return redirect(url_for("admin.packages"))

    items = ServicePackage.query.order_by(ServicePackage.sort_order).all()
    return render_template("admin/packages.html", packages=items)


@admin_bp.route("/citas", methods=["GET", "POST"])
@admin_required
def bookings():
    if request.method == "POST":
        booking = db.session.get(Booking, int(request.form.get("booking_id", 0) or 0))
        if booking:
            new_status = request.form.get("status", booking.status)
            new_pay = request.form.get("payment_status", booking.payment_status)
            booking.status = new_status
            booking.payment_status = new_pay
            booking.admin_notes = request.form.get("admin_notes", booking.admin_notes)
            _audit("booking_update", f"#{booking.id} → {new_status}/{new_pay}")
            db.session.commit()
            notify_booking_status(booking)
            flash(f"Cita #{booking.id} actualizada.", "success")
        return redirect(url_for("admin.bookings"))

    status_filter = request.args.get("status", "")
    query = Booking.query.order_by(Booking.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    items = query.limit(100).all()
    return render_template("admin/bookings.html", bookings=items, status_filter=status_filter)


@admin_bp.route("/comprobante/<int:booking_id>")
@admin_required
def ver_comprobante(booking_id):
    """Muestra el comprobante: URL firmada (Supabase) o archivo local."""
    booking = db.session.get(Booking, booking_id)
    if not booking or not booking.payment_proof:
        abort(404)

    signed = proof_signed_url(booking.payment_proof)
    if signed:
        return redirect(signed)

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    return send_from_directory(upload_dir, booking.payment_proof)


@admin_bp.route("/chats")
@admin_required
def chats():
    """Vista de conversaciones agrupadas por session_id / usuario."""
    messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(200).all()
    # Agrupa por session_id
    threads = {}
    for msg in reversed(messages):
        threads.setdefault(msg.session_id, []).append(msg)
    users = {u.id: u for u in User.query.all()}
    return render_template("admin/chats.html", threads=threads, users=users)
