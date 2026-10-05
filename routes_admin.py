# =============================================================================
# routes_admin.py — Panel administrativo (servicios, citas, chats, packs)
# =============================================================================

import csv
import io
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint,
    Response,
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
from models import AuditLog, Booking, ChatMessage, Review, Service, ServicePackage, User
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


def _parse_pack_form() -> tuple[dict, list[str]]:
    """Parsea el formulario de packs sin permitir 500s."""
    errors: list[str] = []
    name = request.form.get("name", "").strip()
    price, price_error = parse_float(request.form.get("price"), "precio", minimum=0)
    sort_order, sort_error = parse_int(request.form.get("sort_order"), "orden", minimum=0)
    duration, duration_error = parse_int(
        request.form.get("duration_minutes"), "duración (min)", minimum=15
    )
    errors.extend(e for e in (validate_name(name), price_error, sort_error, duration_error) if e)
    fields = {
        "name": name,
        "description": request.form.get("description", "").strip(),
        "includes": request.form.get("includes", "").strip(),
        "price": price,
        "image_url": request.form.get("image_url", "").strip(),
        "sort_order": sort_order,
        "duration_minutes": duration,
    }
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
        fields, errors = _parse_pack_form()
        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("admin.packages"))

        if action == "create":
            pack = ServicePackage(
                name=fields["name"],
                description=fields["description"],
                includes=fields["includes"],
                price=fields["price"],
                currency="NIO",
                duration_minutes=fields["duration_minutes"],
                image_url=fields["image_url"],
                sort_order=fields["sort_order"],
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
                pack.name = fields["name"] or pack.name
                pack.description = fields["description"] or pack.description
                pack.includes = fields["includes"] or pack.includes
                pack.price = fields["price"] if fields["price"] is not None else pack.price
                pack.duration_minutes = fields["duration_minutes"] or pack.duration_minutes
                pack.image_url = fields["image_url"] or pack.image_url
                pack.sort_order = fields["sort_order"] if fields["sort_order"] is not None else pack.sort_order
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
    page = max(request.args.get("page", 1, type=int), 1)
    query = Booking.query.order_by(Booking.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    return render_template(
        "admin/bookings.html",
        bookings=pagination.items,
        status_filter=status_filter,
        pagination=pagination,
    )


@admin_bp.route("/citas/export.csv")
@admin_required
def export_bookings_csv():
    """Export de citas (contabilidad). Respeta el filtro de estado."""
    status_filter = request.args.get("status", "")
    query = Booking.query.order_by(Booking.preferred_date, Booking.preferred_time)
    if status_filter:
        query = query.filter_by(status=status_filter)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "fecha",
            "hora",
            "estado",
            "pago",
            "cliente",
            "email",
            "telefono",
            "servicio",
            "pack",
            "anticipo",
            "notas",
            "creada",
        ]
    )
    for b in query.all():
        writer.writerow(
            [
                b.id,
                b.preferred_date,
                b.preferred_time,
                b.status,
                b.payment_status,
                b.full_name,
                b.email,
                b.phone,
                b.service.name if b.service else "",
                b.package.name if b.package else "",
                f"{b.deposit_amount:.0f}",
                b.admin_notes or b.message or "",
                b.created_at.isoformat(timespec="seconds") if b.created_at else "",
            ]
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    suffix = f"-{status_filter}" if status_filter else ""
    response = Response(
        "\ufeff" + buffer.getvalue(),  # BOM: Excel abre bien los acentos.
        mimetype="text/csv; charset=utf-8",
    )
    response.headers["Content-Disposition"] = f"attachment; filename=citas{suffix}-{stamp}.csv"
    _audit("bookings_export", f"filtro={status_filter or 'todas'}")
    db.session.commit()
    return response


@admin_bp.route("/resenas", methods=["GET", "POST"])
@admin_required
def reviews():
    """Aprobación de reseñas (solo las aprobadas se publican en la portada)."""
    if request.method == "POST":
        review = db.session.get(Review, int(request.form.get("review_id", 0) or 0))
        action = request.form.get("action")
        if review:
            if action == "approve":
                review.is_approved = True
                _audit("review_approve", f"#{review.id} {review.rating}★")
                db.session.commit()
                flash("Reseña publicada en la portada.", "success")
            elif action == "hide":
                review.is_approved = False
                _audit("review_hide", f"#{review.id}")
                db.session.commit()
                flash("Reseña ocultada.", "success")
            elif action == "delete":
                _audit("review_delete", f"#{review.id}")
                db.session.delete(review)
                db.session.commit()
                flash("Reseña eliminada.", "success")
        return redirect(url_for("admin.reviews"))

    items = Review.query.order_by(Review.created_at.desc()).all()
    return render_template(
        "admin/reviews.html",
        reviews=items,
        pending=sum(1 for r in items if not r.is_approved),
    )


@admin_bp.route("/clientas")
@admin_required
def clients():
    """Ficha-listado de clientas: citas, gasto y última visita."""
    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    rows = []
    for user in users:
        bookings = user.bookings
        rows.append(
            {
                "user": user,
                "bookings": len(bookings),
                "active": sum(1 for b in bookings if b.status not in {"cancelled", "completed"}),
                "spent": sum(b.deposit_amount for b in bookings if b.payment_status == "paid"),
                "last": max((b.preferred_date for b in bookings), default="—"),
            }
        )
    return render_template("admin/clients.html", rows=rows)


@admin_bp.route("/clienta/<int:user_id>")
@admin_required
def client_detail(user_id):
    """Historial completo de una clienta."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    bookings = (
        Booking.query.filter_by(user_id=user.id)
        .order_by(Booking.preferred_date.desc(), Booking.preferred_time.desc())
        .all()
    )
    reviews = Review.query.filter_by(user_id=user.id).order_by(Review.created_at.desc()).all()
    stats = {
        "total": len(bookings),
        "completed": sum(1 for b in bookings if b.status == "completed"),
        "active": sum(1 for b in bookings if b.status not in {"cancelled", "completed"}),
        "spent": sum(b.deposit_amount for b in bookings if b.payment_status == "paid"),
        "paid": sum(1 for b in bookings if b.payment_status == "paid"),
    }
    return render_template(
        "admin/client_detail.html", client=user, bookings=bookings, reviews=reviews, stats=stats
    )


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
