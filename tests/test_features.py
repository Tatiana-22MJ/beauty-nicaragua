# =============================================================================
# tests/test_features.py — Duración en la agenda, reseñas, CSV, healthz, recordatorios
# =============================================================================

from datetime import date, timedelta

import notifications
from availability import available_slots, is_slot_free
from extensions import db
from models import Booking, Review, Service, User
from reminders import collect_pending, send_pending, target_date
from tests.conftest import login, make_user


def _future_weekday(target_weekday: int) -> str:
    """Próximo <target_weekday> estrictamente futuro."""
    today = date.today()
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def _next_monday() -> str:
    return _future_weekday(0)


def _mk_booking(app, date_str, time_str, *, status="pending", service=None, user_id=None):
    with app.app_context():
        booking = Booking(
            full_name="Clienta Test",
            email="c@test.ni",
            phone="+505 8877 2117",
            preferred_date=date_str,
            preferred_time=time_str,
            status=status,
            service_id=service.id if service else None,
            user_id=user_id,
        )
        db.session.add(booking)
        db.session.commit()
        return booking.id


def _mk_service(app, name, duration):
    with app.app_context():
        service = Service(
            name=name, description="x", price=100.0,
            duration_minutes=duration, is_active=True, is_seed=False,
        )
        db.session.add(service)
        db.session.commit()
        return service.id


class TestAgendaConDuracion:
    def test_servicio_largo_bloquea_huecos_siguientes(self, app):
        monday = _next_monday()
        with app.app_context():
            service = db.session.get(Service, _mk_service(app, "Balayage Test", 120))
            _mk_booking(app, monday, "09:00", service=service)
            slots = available_slots(monday)
            assert "09:00" not in slots
            assert "10:00" not in slots  # ocupa 09:00–11:00
            assert "11:00" in slots

    def test_servicio_corto_no_bloquea_la_siguiente(self, app):
        monday = _next_monday()
        with app.app_context():
            service = db.session.get(Service, _mk_service(app, "Láser Test", 45))
            _mk_booking(app, monday, "09:00", service=service)
            slots = available_slots(monday)
            assert "09:00" not in slots
            assert "10:00" in slots  # 09:45 ya quedó libre

    def test_no_ofrece_hueco_que_no_cabe_antes_del_cierre(self, app):
        monday = _next_monday()
        with app.app_context():
            slots_60 = available_slots(monday, duration_minutes=60)
            slots_120 = available_slots(monday, duration_minutes=120)
            assert "17:00" in slots_60
            assert "17:00" not in slots_120  # cerraría 19:00
            assert "16:00" in slots_120

    def test_is_slot_free_respeta_duracion(self, app):
        monday = _next_monday()
        with app.app_context():
            assert is_slot_free(monday, "17:00", duration_minutes=60) is True
            assert is_slot_free(monday, "17:00", duration_minutes=120) is False

    def test_api_slots_envia_duracion_del_servicio(self, app, client):
        monday = _next_monday()
        sid = _mk_service(app, "Color Test API", 120)

        plain = client.get(f"/api/slots?date={monday}").get_json()
        assert "17:00" in plain["slots"]

        long_service = client.get(f"/api/slots?date={monday}&service_id={sid}").get_json()
        assert long_service["duration"] == 120
        assert "17:00" not in long_service["slots"]
        assert "16:00" in long_service["slots"]

    def test_reserva_con_servicio_largo_rechaza_hueco_corto(self, app, client):
        uid = make_user(app, "duracion_user", "Clave1234")
        login(client, "duracion_user", "Clave1234")
        sid = _mk_service(app, "Tratamiento 120", 120)
        rv = client.post(
            "/reservar",
            data={
                "full_name": "Clienta Duracion",
                "email": "d@t.ni",
                "phone": "+505 8877 2117",
                "service_id": str(sid),
                "preferred_date": "2099-03-02",  # lunes
                "preferred_time": "17:00",
            },
            follow_redirects=True,
        )
        assert "duración" in rv.get_data(as_text=True)
        with app.app_context():
            assert Booking.query.filter_by(user_id=uid).count() == 0


class TestHealthz:
    def test_healthz_ok(self, client):
        rv = client.get("/healthz")
        payload = rv.get_json()
        assert rv.status_code == 200
        assert payload["status"] == "ok"
        assert payload["database"] == "ok"


class TestResenas:
    def _completed_booking(self, app, username="resena_user"):
        uid = make_user(app, username, "Clave1234")
        with app.app_context():
            booking = Booking(
                full_name="Clienta Reseña",
                email=f"{username}@test.ni",
                phone="+505 8877 2117",
                preferred_date="2099-01-10",
                preferred_time="10:00",
                status="completed",
                user_id=uid,
            )
            db.session.add(booking)
            db.session.commit()
            return booking.id

    def test_no_se_puede_resenar_cita_activa(self, app, client):
        uid = make_user(app, "activa_user", "Clave1234")
        login(client, "activa_user", "Clave1234")
        with app.app_context():
            booking = Booking(
                full_name="A", email="a@t.ni", phone="+505 8877 2117",
                preferred_date="2099-01-11", preferred_time="09:00",
                status="pending", user_id=uid,
            )
            db.session.add(booking)
            db.session.commit()
            bid = booking.id
        rv = client.post(
            f"/mi-cuenta/cita/{bid}/resena",
            data={"rating": "5", "comment": "Genial"},
            follow_redirects=True,
        )
        assert "solo podés reseñar citas completadas" in rv.get_data(as_text=True).lower()

    def test_flujo_completo_publicacion(self, app, client):
        bid = self._completed_booking(app)

        # 1) La clienta reseña → queda pendiente.
        login(client, "resena_user", "Clave1234")
        rv = client.post(
            f"/mi-cuenta/cita/{bid}/resena",
            data={"rating": "5", "comment": "Súper recomendado el spa"},
            follow_redirects=True,
        )
        assert "pendiente" in rv.get_data(as_text=True).lower()
        with app.app_context():
            review = Review.query.filter_by(booking_id=bid).first()
            assert review is not None
            assert review.is_approved is False

        # 2) No publicada todavía en la portada.
        client.get("/logout")
        html = client.get("/").get_data(as_text=True)
        assert "Súper recomendado el spa" not in html

        # 3) Admin aprueba → aparece en la portada.
        make_user(app, "admin_res", "Clave1234", is_admin=True)
        login(client, "admin_res", "Clave1234")
        with app.app_context():
            rid = Review.query.filter_by(booking_id=bid).first().id
        rv = client.post(
            "/admin/resenas",
            data={"review_id": str(rid), "action": "approve"},
            follow_redirects=True,
        )
        assert "publicada" in rv.get_data(as_text=True).lower()
        client.get("/logout")
        html = client.get("/").get_data(as_text=True)
        assert "Súper recomendado el spa" in html

    def test_rating_invalido_rechazado(self, app, client):
        bid = self._completed_booking(app, "rating_user")
        login(client, "rating_user", "Clave1234")
        rv = client.post(
            f"/mi-cuenta/cita/{bid}/resena",
            data={"rating": "9", "comment": "x"},
            follow_redirects=True,
        )
        assert "1 a 5" in rv.get_data(as_text=True)
        with app.app_context():
            assert Review.query.filter_by(booking_id=bid).count() == 0


class TestAdminExportYClientes:
    def _admin(self, app, client, username="admin_csv"):
        make_user(app, username, "Clave1234", is_admin=True)
        login(client, username, "Clave1234")

    def test_export_csv_requiere_admin(self, app, client):
        make_user(app, "no_admin_csv", "Clave1234")
        login(client, "no_admin_csv", "Clave1234")
        assert client.get("/admin/citas/export.csv").status_code == 403

    def test_export_csv_contenido(self, app, client):
        self._admin(app, client)
        _mk_booking(app, "2099-02-02", "09:00")
        rv = client.get("/admin/citas/export.csv")
        assert rv.status_code == 200
        assert "text/csv" in rv.content_type
        body = rv.get_data(as_text=True)
        assert "id,fecha,hora" in body.replace("\ufeff", "")
        assert "2099-02-02" in body

    def test_listado_y_ficha_de_clientas(self, app, client):
        self._admin(app, client, "admin_cli")
        uid = make_user(app, "clienta_hist", "Clave1234")
        _mk_booking(app, "2099-02-03", "10:00", user_id=uid, status="completed")

        rv = client.get("/admin/clientas")
        assert rv.status_code == 200
        assert "clienta_hist" in rv.get_data(as_text=True) or "Clienta clienta_hist" in rv.get_data(as_text=True)

        rv = client.get(f"/admin/clienta/{uid}")
        assert rv.status_code == 200
        html = rv.get_data(as_text=True)
        assert "2099-02-03" in html
        assert "Citas totales" in html


class TestRecordatorios:
    def _booking_for_tomorrow(self, app, status="pending"):
        with app.app_context():
            booking = Booking(
                full_name="Mañana Test",
                email="m@test.ni",
                phone="+505 8877 2117",
                preferred_date=target_date(),
                preferred_time="10:00",
                status=status,
            )
            db.session.add(booking)
            db.session.commit()
            return booking.id

    def test_collect_pending_solo_activas_sin_recordatorio(self, app):
        bid = self._booking_for_tomorrow(app)
        with app.app_context():
            pending_ids = [b.id for b in collect_pending()]
            assert bid in pending_ids

            booking = db.session.get(Booking, bid)
            booking.status = "cancelled"
            db.session.commit()
            assert bid not in [b.id for b in collect_pending()]

    def test_send_pending_marca_recordatorio(self, app):
        bid = self._booking_for_tomorrow(app)
        with app.app_context():
            result = send_pending()
            assert result["sent"] >= 1
            booking = db.session.get(Booking, bid)
            assert booking.reminder_sent_at is not None
            # Segunda corrida: ya no está pendiente.
            assert bid not in [b.id for b in collect_pending()]

    def test_dry_run_no_envia(self, app):
        bid = self._booking_for_tomorrow(app, status="confirmed")
        with app.app_context():
            send_pending(dry_run=True)
            booking = db.session.get(Booking, bid)
            assert booking.reminder_sent_at is None


class TestObservabilidad:
    def test_500_no_explota_en_template(self, client):
        assert client.get("/").status_code == 200

    def test_healthz_sin_login(self, client):
        # healthz debe funcionar sin sesión (lo usan los health checks).
        assert client.get("/healthz").status_code == 200


def test_usuarios_admin_y_clientas_separados(app):
    with app.app_context():
        assert User.query.filter_by(is_admin=True).count() >= 1


class TestPagoQR:
    """Datos de pago configurables por .env (no hardcodeados en templates)."""

    @staticmethod
    def _ver_detalle(app, client, username, **config):
        for key, value in config.items():
            app.config[key] = value
        uid = make_user(app, username, "Clave1234")
        login(client, username, "Clave1234")
        bid = _mk_booking(app, _next_monday(), "14:00", user_id=uid)
        return client.get(f"/mi-cuenta/cita/{bid}")

    def test_cuenta_bancaria_configurable(self, app, client):
        rv = self._ver_detalle(
            app, client, "pago_cfg", BANK_ACCOUNT="TEST-9999", BANK_HOLDER="Otra Dueña"
        )
        assert rv.status_code == 200
        assert b"TEST-9999" in rv.data
        assert "Otra Dueña".encode() in rv.data

    def test_link_y_qr_se_muestran_si_estan_configurados(self, app, client):
        rv = self._ver_detalle(
            app,
            client,
            "pago_link",
            PAYMENT_LINK="https://pay.example/x",
            PAYMENT_QR_URL="https://img.example/qr.png",
            PAYMENT_PHONE="8888-7777",
            PAYMENT_REFERENCE="Usa tu cedula",
        )
        assert b"https://pay.example/x" in rv.data
        assert b"https://img.example/qr.png" in rv.data
        assert b"8888-7777" in rv.data
        assert b"Usa tu cedula" in rv.data

    def test_link_y_qr_ocultos_sin_configurar(self, app, client):
        rv = self._ver_detalle(
            app, client, "pago_vacio", PAYMENT_LINK="", PAYMENT_QR_URL=""
        )
        assert rv.status_code == 200
        assert "Pagar en línea".encode() not in rv.data
        assert b"qr-pago" not in rv.data


class TestComprobanteSoloAlConfirmar:
    """El PDF de reserva NO se entrega al reservar: recién al confirmar."""

    @staticmethod
    def _espiar(monkeypatch):
        llamadas = []

        def fake_send_email(to, subject, body, attachment_name=None, attachment_bytes=None):
            llamadas.append((to, attachment_name, attachment_bytes))
            return True

        monkeypatch.setattr(notifications, "send_email", fake_send_email)
        monkeypatch.setattr(notifications, "send_whatsapp_message", lambda *a, **k: True)
        return llamadas

    @staticmethod
    def _de_clienta(llamadas):
        return [c for c in llamadas if c[0] == "c@test.ni"]

    def test_al_reservar_no_se_adjunta_pdf(self, app, monkeypatch):
        llamadas = self._espiar(monkeypatch)
        bid = _mk_booking(app, _next_monday(), "10:00")
        with app.app_context():
            notifications.notify_booking_created(db.session.get(Booking, bid))
        cliente = self._de_clienta(llamadas)
        assert len(cliente) == 1
        assert cliente[0][1] is None
        assert cliente[0][2] is None

    def test_al_confirmar_se_adjunta_pdf(self, app, monkeypatch):
        llamadas = self._espiar(monkeypatch)
        bid = _mk_booking(app, _next_monday(), "11:00", status="confirmed")
        with app.app_context():
            notifications.notify_booking_status(db.session.get(Booking, bid))
        cliente = self._de_clienta(llamadas)
        assert len(cliente) == 1
        assert cliente[0][1] == "reserva-beauty.pdf"
        assert cliente[0][2].startswith(b"%PDF")

    def test_al_cancelar_no_se_adjunta_pdf(self, app, monkeypatch):
        llamadas = self._espiar(monkeypatch)
        bid = _mk_booking(app, _next_monday(), "12:00", status="cancelled")
        with app.app_context():
            notifications.notify_booking_status(db.session.get(Booking, bid))
        cliente = self._de_clienta(llamadas)
        assert len(cliente) == 1
        assert cliente[0][1] is None
