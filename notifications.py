# =============================================================================
# notifications.py — Email (SMTP o log) + helpers WhatsApp
# =============================================================================

import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

import requests
from flask import current_app

logger = logging.getLogger("beauty.notifications")


def normalize_whatsapp_number(number: str | None) -> str:
    cleaned = (number or "").replace("+", "").replace(" ", "").replace("-", "")
    if cleaned.startswith("505"):
        return cleaned
    if cleaned.startswith("0"):
        return f"505{cleaned[1:]}"
    return f"505{cleaned}"


def whatsapp_link(message: str | None = None, number: str | None = None) -> str:
    """Deep link wa.me con mensaje precargado (Nicaragua +505)."""
    normalized = normalize_whatsapp_number(number or current_app.config.get("WHATSAPP_NUMBER", "50576721749"))
    text = message or current_app.config.get("WHATSAPP_DEFAULT_MSG", "Hola Beauty")
    return f"https://wa.me/{normalized}?text={quote(text)}"


def send_whatsapp_message(to_phone: str, message: str, *, attachment_url: str | None = None) -> bool:
    """Envía un mensaje WhatsApp si están configuradas credenciales Twilio; si no, deja un deep-link útil en logs."""
    twilio_sid = current_app.config.get("TWILIO_ACCOUNT_SID", "")
    twilio_token = current_app.config.get("TWILIO_AUTH_TOKEN", "")
    twilio_from = current_app.config.get("TWILIO_WHATSAPP_FROM", "")
    if twilio_sid and twilio_token and twilio_from:
        try:
            payload = {
                "From": twilio_from,
                "To": f"whatsapp:+{normalize_whatsapp_number(to_phone)}",
                "Body": message,
            }
            if attachment_url:
                payload["MediaUrl"] = attachment_url
            response = requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json",
                data=payload,
                auth=(twilio_sid, twilio_token),
                timeout=20,
            )
            response.raise_for_status()
            logger.info("WhatsApp enviado a %s", to_phone)
            return True
        except Exception:
            logger.exception("Fallo al enviar WhatsApp a %s", to_phone)
            return False

    logger.info("[WHATSAPP-LINK] to=%s url=%s", to_phone, whatsapp_link(message, to_phone))
    return True


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_booking_pdf(booking) -> bytes:
    """Genera un comprobante mínimo en PDF para la reserva."""
    title = booking.title
    when = f"{booking.preferred_date} {booking.preferred_time}"
    lines = [
        "Beauty Nicaragua",
        "Comprobante de reserva",
        "",
        f"Cliente: {booking.full_name}",
        f"Email: {booking.email}",
        f"Teléfono: {booking.phone}",
        f"Servicio: {title}",
        f"Fecha/Hora: {when}",
        f"Estado: {booking.status}",
        f"Pago: {booking.payment_status}",
        f"Anticipo sugerido: C$ {booking.deposit_amount:,.0f}",
        f"Mensaje: {booking.message or '—'}",
        "",
        "Gracias por elegir Beauty Nicaragua.",
    ]
    content_stream = "BT\n/F1 12 Tf\n36 780 Td\n"
    for line in lines:
        content_stream += f"({_pdf_escape(line)}) Tj\n0 -18 Td\n"
    content_stream += "ET\n"

    content_bytes = content_stream.encode("latin-1", errors="ignore")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content_bytes)} >>\nstream\n".encode("latin-1") + content_bytes + b"\nendstream",
    ]

    pdf_parts = [b"%PDF-1.4\n"]
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(b"".join(pdf_parts)))
        pdf_parts.append(f"{idx} 0 obj\n".encode("latin-1"))
        pdf_parts.append(obj)
        pdf_parts.append(b"\nendobj\n")

    xref_start = len(b"".join(pdf_parts))
    pdf_parts.append(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf_parts.append(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf_parts.append(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf_parts.append(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("latin-1"))
    return b"".join(pdf_parts)


def send_email(to: str, subject: str, body: str, attachment_name: str | None = None, attachment_bytes: bytes | None = None) -> bool:
    """
    Envía email si MAIL_ENABLED=1 o si hay credenciales SMTP cargadas.
    Si no hay SMTP configurado, se deja traza en logs (dev-friendly).
    Retorna True si se envió o se registró correctamente.
    """
    sender = current_app.config.get("MAIL_DEFAULT_SENDER", "info@beauty-nicaragua.com")
    mail_enabled = bool(current_app.config.get("MAIL_ENABLED"))
    user = current_app.config.get("MAIL_USERNAME", "")
    password = current_app.config.get("MAIL_PASSWORD", "")
    if not mail_enabled and not (user and password):
        logger.info("[EMAIL-MOCK] to=%s subject=%s\n%s", to, subject, body)
        if attachment_name and attachment_bytes:
            logger.info("[EMAIL-MOCK-ATTACHMENT] %s bytes=%d", attachment_name, len(attachment_bytes))
        return True

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    if attachment_name and attachment_bytes:
        msg.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype="pdf",
            filename=attachment_name,
        )

    try:
        server = current_app.config["MAIL_SERVER"]
        port = current_app.config["MAIL_PORT"]
        with smtplib.SMTP(server, port, timeout=20) as smtp:
            if current_app.config.get("MAIL_USE_TLS"):
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
        logger.info("Email enviado a %s", to)
        return True
    except Exception:
        logger.exception("Fallo al enviar email a %s", to)
        return False


def notify_booking_created(booking) -> None:
    """Avisa a clienta y admin cuando hay nueva reserva."""
    title = booking.title
    when = f"{booking.preferred_date} {booking.preferred_time}"
    confirmation_pdf = build_booking_pdf(booking)
    whatsapp_text = (
        f"Hola Beauty, quiero confirmar mi cita de {title} el {when}. "
        f"Mi nombre es {booking.full_name} y mi teléfono es {booking.phone}."
    )
    whatsapp_url = whatsapp_link(whatsapp_text, current_app.config.get("WHATSAPP_NUMBER", "50576721749"))
    client_body = (
        f"Hola {booking.full_name},\n\n"
        f"Recibimos tu solicitud de cita para «{title}» el {when}.\n"
        f"Estado: {booking.status}. Pago: {booking.payment_status}.\n"
        f"Anticipo sugerido: C$ {booking.deposit_amount:,.0f}.\n\n"
        f"Te confirmaremos pronto. También podés escribirnos por WhatsApp usando este enlace:\n"
        f"{whatsapp_url}\n\n"
        f"Adjuntamos tu comprobante PDF de reserva.\n"
        f"— Beauty Nicaragua (Managua)"
    )
    send_email(
        booking.email,
        f"Solicitud recibida — {title}",
        client_body,
        attachment_name="reserva-beauty.pdf",
        attachment_bytes=confirmation_pdf,
    )
    send_whatsapp_message(booking.phone, whatsapp_text)

    admin_to = current_app.config.get("ADMIN_NOTIFY_EMAIL")
    if admin_to:
        admin_body = (
            f"Nueva reserva #{booking.id}\n"
            f"Clienta: {booking.full_name} ({booking.email} / {booking.phone})\n"
            f"Servicio: {title}\n"
            f"Cuando: {when}\n"
            f"Mensaje: {booking.message or '—'}\n"
            f"WhatsApp link: {whatsapp_url}\n"
        )
        send_email(admin_to, f"[Beauty] Nueva cita #{booking.id}", admin_body)


def notify_booking_status(booking) -> None:
    """Notifica cambio de estado (confirmada / cancelada / reprogramar)."""
    title = booking.title
    when = f"{booking.preferred_date} {booking.preferred_time}"
    body = (
        f"Hola {booking.full_name},\n\n"
        f"Tu cita «{title}» ({when}) ahora está: {booking.status.upper()}.\n"
        f"Pago: {booking.payment_status}.\n"
        f"{booking.admin_notes and 'Nota: ' + booking.admin_notes + chr(10) or ''}"
        f"\n— Beauty Nicaragua"
    )
    send_email(booking.email, f"Actualización de cita — {booking.status}", body)
