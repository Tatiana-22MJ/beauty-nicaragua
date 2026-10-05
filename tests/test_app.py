# =============================================================================
# tests/test_app.py — Rutas públicas, auth, reservas y restablecimiento
# =============================================================================

from extensions import db
from models import Booking, Service, User
from tests.conftest import login, make_user


class TestRutasPublicas:
    def test_index_200(self, client):
        assert client.get("/").status_code == 200

    def test_privacidad_y_terminos(self, client):
        assert client.get("/privacidad").status_code == 200
        assert client.get("/terminos").status_code == 200

    def test_404_template(self, client):
        assert client.get("/ruta-inexistente").status_code == 404

    def test_security_headers(self, client):
        rv = client.get("/")
        assert rv.headers.get("X-Content-Type-Options") == "nosniff"
        assert rv.headers.get("X-Frame-Options") == "DENY"

    def test_api_slots_rechaza_fecha_invalida(self, client):
        rv = client.get("/api/slots?date=not-a-date")
        assert rv.status_code == 400

    def test_precio_nio_en_html(self, client):
        html = client.get("/").get_data(as_text=True)
        assert "C$" in html  # moneda localizada


class TestAuth:
    def test_registro_y_login(self, client, app):
        rv = client.post(
            "/registro",
            data={
                "full_name": "María Test",
                "username": "maria_test",
                "email": "maria@test.ni",
                "phone": "+505 8877 2117",
                "password": "Clave1234",
                "confirm_password": "Clave1234",
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        with app.app_context():
            assert User.query.filter_by(username="maria_test").first() is not None

    def test_login_incorrecto(self, client):
        make_user(client.application, "ana", "Clave1234")
        rv = login(client, "ana", "wrongpass")
        assert "incorrectos" in rv.get_data(as_text=True)

    def test_mi_cuenta_requiere_login(self, client):
        rv = client.get("/mi-cuenta/", follow_redirects=False)
        assert rv.status_code == 302

    def test_admin_requiere_rol(self, client):
        make_user(client.application, "noadmin", "Clave1234")
        login(client, "noadmin", "Clave1234")
        assert client.get("/admin/").status_code == 403


class TestReservas:
    def _reserva_data(self):
        return {
            "full_name": "Clienta Test",
            "email": "clienta@test.ni",
            "phone": "+505 8877 2117",
            "service_id": "",
            "package_id": "",
            "preferred_date": "",
            "preferred_time": "",
            "message": "primera visita",
        }

    def test_reserva_requiere_login(self, client):
        rv = client.post("/reservar", data=self._reserva_data(), follow_redirects=False)
        assert rv.status_code == 302

    def test_reserva_sin_servicio_rechazada(self, client):
        make_user(client.application, "carla", "Clave1234")
        login(client, "carla", "Clave1234")
        data = self._reserva_data()
        data["preferred_date"] = "2099-01-15"
        data["preferred_time"] = "09:00"
        rv = client.post("/reservar", data=data, follow_redirects=True)
        assert "Selecciona un servicio" in rv.get_data(as_text=True)

    def test_reserva_exitosa(self, client, app):
        uid = make_user(app, "lucia", "Clave1234")
        login(client, "lucia", "Clave1234")

        with app.app_context():
            service = Service(
                name="Test Service", description="x", price=100.0,
                duration_minutes=60, is_active=True, is_seed=False,
            )
            db.session.add(service)
            db.session.commit()
            sid = service.id

        data = self._reserva_data()
        data["service_id"] = str(sid)
        data["preferred_date"] = "2099-01-15"
        data["preferred_time"] = "09:00"
        rv = client.post("/reservar", data=data, follow_redirects=True)
        assert "Cita solicitada" in rv.get_data(as_text=True)
        with app.app_context():
            b = Booking.query.filter_by(user_id=uid, preferred_date="2099-01-15").first()
            assert b is not None
            assert b.status == "pending"

    def test_horario_ocupado_rechazado(self, client, app):
        make_user(app, "paula", "Clave1234")
        login(client, "paula", "Clave1234")

        with app.app_context():
            service = Service(name="S2", description="x", price=50.0, is_active=True)
            db.session.add(service)
            db.session.add(
                Booking(
                    full_name="Otra", email="o@o.ni", phone="+505 0000 0000",
                    preferred_date="2099-01-16", preferred_time="10:00",
                    status="pending",
                )
            )
            db.session.commit()
            sid = service.id

        data = self._reserva_data()
        data["service_id"] = str(sid)
        data["preferred_date"] = "2099-01-16"
        data["preferred_time"] = "10:00"
        rv = client.post("/reservar", data=data, follow_redirects=True)
        assert "ocupado" in rv.get_data(as_text=True)


class TestRestablecimiento:
    def test_solicitud_no_revela_existencia(self, client):
        make_user(client.application, "existente", "Clave1234")
        rv = client.post(
            "/recuperar",
            data={"identifier": "existente"},
            follow_redirects=True,
        )
        assert "Si la cuenta existe" in rv.get_data(as_text=True)

    def test_token_invalido_rechazado(self, client):
        rv = client.get("/restablecer/token-falso-123", follow_redirects=True)
        assert "no es válido" in rv.get_data(as_text=True)

    def test_flujo_completo_reset(self, client, app):
        make_user(app, "daniela", "OldPass123")

        # 1) Solicitar token (el email se registra en logs en modo test).
        client.post("/recuperar", data={"identifier": "daniela"})

        # 2) Generar el token directamente (mismo mecanismo que la ruta).
        from app import RESET_SALT
        from itsdangerous import URLSafeTimedSerializer

        with app.app_context():
            user = User.query.filter_by(username="daniela").first()
            serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt=RESET_SALT)
            token = serializer.dumps(user.id)

        # 3) Cambiar la contraseña.
        rv = client.post(
            f"/restablecer/{token}",
            data={"password": "NewPass123", "confirm_password": "NewPass123"},
            follow_redirects=True,
        )
        assert "actualizada" in rv.get_data(as_text=True)

        # 4) Login con la nueva clave.
        rv = login(client, "daniela", "NewPass123")
        assert "Hola de nuevo" in rv.get_data(as_text=True)


class TestSeed:
    def test_seed_crea_catalogo(self, app):
        with app.app_context():
            assert Service.query.filter_by(is_seed=True).count() >= 8

    def test_admin_creado(self, app):
        with app.app_context():
            admin = User.query.filter_by(is_admin=True).first()
            assert admin is not None
