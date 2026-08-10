# =============================================================================
# routes_admin.py — Panel administrativo (servicios, citas, chats, packs)
# =============================================================================

from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import AuditLog, Booking, ChatMessage, Service, ServicePackage, User
from notifications import notify_booking_status

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


@admin_bp.route("/servicios", methods=["GET", "POST"])
@admin_required
def services():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            service = Service(
                name=request.form.get("name", "").strip(),
                description=request.form.get("description", "").strip(),
                price=float(request.form.get("price") or 0),
                currency="NIO",
                duration_minutes=int(request.form.get("duration_minutes") or 60),
                icon=request.form.get("icon", "✨").strip() or "✨",
                image_url=request.form.get("image_url", "").strip(),
                sort_order=int(request.form.get("sort_order") or 0),
                quote_only=request.form.get("quote_only") == "on",
                is_active=True,
            )
            db.session.add(service)
            _audit("service_create", service.name)
            db.session.commit()
            flash("Servicio creado.", "success")
        elif action == "update":
            service = db.session.get(Service, int(request.form.get("service_id")))
            if service:
                service.name = request.form.get("name", service.name).strip()
                service.description = request.form.get("description", service.description).strip()
                service.price = float(request.form.get("price") or service.price)
                service.duration_minutes = int(request.form.get("duration_minutes") or service.duration_minutes)
                service.icon = request.form.get("icon", service.icon).strip()
                service.image_url = request.form.get("image_url", service.image_url).strip()
                service.sort_order = int(request.form.get("sort_order") or service.sort_order)
                service.quote_only = request.form.get("quote_only") == "on"
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
        if action == "create":
            pack = ServicePackage(
                name=request.form.get("name", "").strip(),
                description=request.form.get("description", "").strip(),
                includes=request.form.get("includes", "").strip(),
                price=float(request.form.get("price") or 0),
                currency="NIO",
                image_url=request.form.get("image_url", "").strip(),
                sort_order=int(request.form.get("sort_order") or 0),
                is_active=True,
            )
            db.session.add(pack)
            _audit("package_create", pack.name)
            db.session.commit()
            flash("Pack creado.", "success")
        elif action == "update":
            pack = db.session.get(ServicePackage, int(request.form.get("package_id")))
            if pack:
                pack.name = request.form.get("name", pack.name).strip()
                pack.description = request.form.get("description", pack.description).strip()
                pack.includes = request.form.get("includes", pack.includes).strip()
                pack.price = float(request.form.get("price") or pack.price)
                pack.image_url = request.form.get("image_url", pack.image_url).strip()
                pack.sort_order = int(request.form.get("sort_order") or pack.sort_order)
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
        booking = db.session.get(Booking, int(request.form.get("booking_id")))
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
