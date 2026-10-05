# =============================================================================
# tests/conftest.py — Fixtures de la suite (SQLite temporal por test)
# =============================================================================

import pytest

from app import create_app
from config import Config
from extensions import db as _db
from models import User


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SECRET_KEY = "test-secret-key-not-for-production"


@pytest.fixture()
def app(tmp_path):
    """App de prueba con BD SQLite en archivo temporal (aislada por test)."""

    class TestAppConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
        UPLOAD_FOLDER = str(tmp_path / "uploads")

    application = create_app(TestAppConfig)
    application.config["TEST_DB_PATH"] = str(tmp_path / "test.db")
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    with app.app_context():
        yield _db


def make_user(app, username="clienta1", password="Clave1234", is_admin=False):
    """Crea y devuelve un usuario de prueba (id)."""
    with app.app_context():
        user = User(
            username=username,
            email=f"{username}@test.ni",
            full_name=f"Clienta {username}",
            phone="+505 8877 2117",
            is_admin=is_admin,
        )
        user.set_password(password)
        _db.session.add(user)
        _db.session.commit()
        return user.id


def login(client, identifier: str, password: str):
    return client.post(
        "/login",
        data={"identifier": identifier, "password": password},
        follow_redirects=True,
    )
