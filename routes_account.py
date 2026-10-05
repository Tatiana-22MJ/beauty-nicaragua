# =============================================================================
# routes_account.py — Área de clienta: mis citas, cancelar, reprogramar, pago
# =============================================================================

import uuid
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from availability import available_slots, booking_duration_minutes, is_slot_free
from extensions import db, limiter
from models import AuditLog, Booking, Review, Service, ServicePackage
from notifications import notify_booking_status, whatsapp_link
from supabase_storage import upload_proof as upload_proof_to_supabase
from validators import validate_date, validate_file_signature, validate_rating, validate_time

account_bp = Blueprint("account", __name__, url_prefix="/mi-cuenta")


def _allowed_proof(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_PROOF_EXTENSIONS"]


@account_bp.route("/")
@login_required
def dashboard():
    """Lista las citas de la usuaria autenticada."""
    bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.preferred_date.asc(), Booking.preferred_time.asc())
        .all()
    )
    upcoming = next((b for b in bookings if b.status not in {"cancelled", "completed"}), None)
    return render_template(
        "account/dashboard.html",
        bookings=bookings,
        stats={
            "citas": len(bookings),
            "pendientes": sum(1 for b in bookings if b.status not in {"cancelled", "completed"}),
            "reprogramadas": sum(1 for b in bookings if b.status == "reschedule"),
        },
        upcoming_booking=upcoming,
        wa_link=whatsapp_link(f"Hola, soy {current_user.full_name}. Consulto sobre mi cita."),
        bank_name=current_app.config["BANK_NAME"],
        bank_account=current_app.config["BANK_ACCOUNT"],
        bank_holder=current_app.config["BANK_HOLDER"],
    )


@account_bp.route("/cita/<int:booking_id>")
@login_required
def booking_detail(booking_id):
    """Detalle de una cita propia (la plantilla ya existía sin ruta)."""
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        flash("Cita no encontrada.", "error")
        return redirect(url_for("account.dashboard"))
    wa_link = whatsapp_link(
        f"Hola, soy {current_user.full_name}. Consulto sobre mi cita #{booking.id}."
    )
    return render_template("account/booking_detail.html", booking=booking, wa_link=wa_link)


@account_bp.route("/cita/<int:booking_id>/cancelar", methods=["POST"])
@login_required
@limiter.limit("20 per hour")
def cancel_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        flash("Cita no encontrada.", "error")
        return redirect(url_for("account.dashboard"))
    if booking.status in ("cancelled", "completed"):
        flash("Esta cita ya no se puede cancelar.", "error")
        return redirect(url_for("account.dashboard"))
    booking.status = "cancelled"
    db.session.commit()
    notify_booking_status(booking)
    flash("Cita cancelada.", "success")
    return redirect(url_for("account.dashboard"))


@account_bp.route("/cita/<int:booking_id>/reprogramar", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per hour")
def reschedule_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        flash("Cita no encontrada.", "error")
        return redirect(url_for("account.dashboard"))
    if booking.status in ("cancelled", "completed"):
        flash("Esta cita no se puede reprogramar.", "error")
        return redirect(url_for("account.dashboard"))

    if request.method == "POST":
        new_date = request.form.get("preferred_date", "").strip()
        new_time = request.form.get("preferred_time", "").strip()
        duration = booking_duration_minutes(booking)
        errors = [e for e in (validate_date(new_date), validate_time(new_time)) if e]
        if not errors and not is_slot_free(
            new_date, new_time, duration_minutes=duration, exclude_booking_id=booking.id
        ):
            errors.append("Ese horario ya no está disponible (o no alcanza para la duración).")
        if errors:
            for e in errors:
                flash(e, "error")
            return redirect(url_for("account.reschedule_booking", booking_id=booking.id))

        booking.preferred_date = new_date
        booking.preferred_time = new_time
        booking.status = "reschedule"
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Ese horario acaba de ser reservado. Elegí otro, por favor.", "error")
            return redirect(url_for("account.reschedule_booking", booking_id=booking.id))
        notify_booking_status(booking)
        flash("Solicitud de reprogramación enviada. Te confirmaremos pronto.", "success")
        return redirect(url_for("account.dashboard"))

    slots = available_slots(
        booking.preferred_date,
        duration_minutes=booking_duration_minutes(booking),
        exclude_booking_id=booking.id,
    )
    return render_template("account/reschedule.html", booking=booking, slots=slots)


@account_bp.route("/cita/<int:booking_id>/comprobante", methods=["POST"])
@login_required
@limiter.limit("15 per hour")
def upload_proof(booking_id):
    """Sube comprobante de transferencia (anticipo)."""
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        flash("Cita no encontrada.", "error")
        return redirect(url_for("account.dashboard"))

    file = request.files.get("payment_proof")
    if not file or not file.filename:
        flash("Seleccioná un archivo de comprobante.", "error")
        return redirect(url_for("account.dashboard"))
    if not _allowed_proof(file.filename):
        flash("Formato no permitido. Usá PNG, JPG, WEBP o PDF.", "error")
        return redirect(url_for("account.dashboard"))

    # Validar el CONTENIDO real (magic bytes), no solo la extensión:
    # evita subir ejecutables renombrados a .png.
    signature_error = validate_file_signature(file.stream, file.filename)
    if signature_error:
        flash(signature_error, "error")
        return redirect(url_for("account.dashboard"))

    ext = secure_filename(file.filename).rsplit(".", 1)[-1].lower()
    filename = f"proof_{booking.id}_{uuid.uuid4().hex[:8]}.{ext}"
    data = file.read()

    # Preferencia: Supabase Storage (persistente entre deploys). Fallback: disco local.
    stored_path = upload_proof_to_supabase(data, filename, content_type=file.mimetype or "application/octet-stream")
    if stored_path:
        booking.payment_proof = stored_path
    else:
        upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
        upload_dir.mkdir(parents=True, exist_ok=True)
        (upload_dir / filename).write_bytes(data)
        booking.payment_proof = filename

    booking.payment_status = "pending_transfer"
    db.session.commit()
    flash("Comprobante recibido. Validaremos el anticipo pronto.", "success")
    return redirect(url_for("account.dashboard"))


@account_bp.route("/cita/<int:booking_id>/resena", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def submit_review(booking_id):
    """Reseña de una cita completada (queda pendiente de aprobación admin)."""
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        flash("Cita no encontrada.", "error")
        return redirect(url_for("account.dashboard"))
    if booking.status != "completed":
        flash("Solo podés reseñar citas completadas.", "error")
        return redirect(url_for("account.dashboard"))
    if booking.review:
        flash("Ya dejaste una reseña para esta cita.", "error")
        return redirect(url_for("account.dashboard"))

    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment", "").strip()
    error = validate_rating(rating, comment)
    if error:
        flash(error, "error")
        return redirect(url_for("account.dashboard"))

    db.session.add(
        Review(
            booking_id=booking.id,
            user_id=current_user.id,
            rating=rating,
            comment=comment,
            is_approved=False,
        )
    )
    db.session.commit()
    flash("¡Gracias por tu reseña! La publicaremos cuando la revisemos.", "success")
    return redirect(url_for("account.dashboard"))
