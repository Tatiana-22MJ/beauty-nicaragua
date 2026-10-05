# =============================================================================
# tests/test_availability.py — Agenda: días cerrados, slots y zona Managua
# =============================================================================

from datetime import date, datetime, timedelta

from availability import available_slots, day_window, is_slot_free
from extensions import db
from models import Booking


def _future_weekday(target_weekday: int) -> str:
    """Próximo <target_weekday> ESTRICTAMENTE futuro (si hoy es ese día, +7).

    Evita usar "hoy": los slots ya pasados de hoy se filtran por la agenda.
    """
    today = date.today()
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def _next_saturday() -> str:
    return _future_weekday(5)


def _next_sunday() -> str:
    return _future_weekday(6)


def _next_monday() -> str:
    return _future_weekday(0)


class TestDayWindow:
    def test_sabado_cierre_temprano(self):
        window = day_window(_next_saturday())
        assert window == (__import__("datetime").time(8, 0), __import__("datetime").time(14, 0))

    def test_domingo_cerrado(self):
        assert day_window(_next_sunday()) is None

    def test_entre_semana_hasta_18(self):
        window = day_window(_next_monday())
        assert window == (__import__("datetime").time(8, 0), __import__("datetime").time(18, 0))

    def test_fecha_invalida(self):
        assert day_window("no-una-fecha") is None


class TestSlots:
    def test_domingo_sin_slots(self, app):
        with app.app_context():
            assert available_slots(_next_sunday()) == []

    def test_slots_generados(self, app):
        with app.app_context():
            slots = available_slots(_next_monday())
            assert "08:00" in slots
            assert "17:00" in slots
            assert "18:00" not in slots  # end exclusive

    def test_slot_ocupado_no_se_ofrece(self, app):
        with app.app_context():
            monday = _next_monday()
            booking = Booking(
                full_name="Test", email="t@t.ni", phone="+505 0000 0000",
                service_id=None, package_id=None,
                preferred_date=monday, preferred_time="09:00", status="pending",
            )
            db.session.add(booking)
            db.session.commit()
            slots = available_slots(monday)
            assert "09:00" not in slots

    def test_cancelacion_libera_slot(self, app):
        with app.app_context():
            monday = _next_monday()
            booking = Booking(
                full_name="Test", email="t@t.ni", phone="+505 0000 0000",
                preferred_date=monday, preferred_time="10:00", status="cancelled",
            )
            db.session.add(booking)
            db.session.commit()
            assert "10:00" in available_slots(monday)


class TestAntiDobleReserva:
    """El índice único parcial debe impedir dos citas activas idénticas."""

    def _mk(self, date_str, time_str, status="pending"):
        return Booking(
            full_name="Test", email="t@t.ni", phone="+505 0000 0000",
            preferred_date=date_str, preferred_time=time_str, status=status,
        )

    def test_doble_reserva_activa_bloqueada(self, app):
        with app.app_context():
            monday = _next_monday()
            db.session.add(self._mk(monday, "11:00"))
            db.session.commit()
            db.session.add(self._mk(monday, "11:00"))
            try:
                db.session.commit()
                raised = False
            except Exception:
                raised = True
            db.session.rollback()
            assert raised, "El índice único no bloqueó la doble reserva activa"

    def test_completada_permite_reusar_hueco(self, app):
        with app.app_context():
            monday = _next_monday()
            db.session.add(self._mk(monday, "12:00", status="completed"))
            db.session.commit()
            db.session.add(self._mk(monday, "12:00"))  # activa sobre hueco completado
            try:
                db.session.commit()
                raised = False
            except Exception:
                raised = True
            db.session.rollback()
            assert not raised, "Una cita completada debe liberar el hueco"

    def test_is_slot_free_integra(self, app):
        with app.app_context():
            monday = _next_monday()
            db.session.add(self._mk(monday, "13:00"))
            db.session.commit()
            assert is_slot_free(monday, "13:00") is False
            assert is_slot_free(monday, "14:00") is True  # agenda en hora en punto
