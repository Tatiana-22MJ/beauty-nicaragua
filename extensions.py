# =============================================================================
# extensions.py — Extensiones Flask compartidas (evita imports circulares)
# =============================================================================

from flask_limiter import Limiter  # Rate limiting (anti fuerza bruta / abuso chat).
from flask_limiter.util import get_remote_address  # Clave de límite = IP del cliente.
from flask_login import LoginManager  # Sesiones de usuario.
from flask_migrate import Migrate  # Migraciones Alembic vía Flask-Migrate.
from flask_socketio import SocketIO  # WebSockets del chat.
from flask_sqlalchemy import SQLAlchemy  # ORM.
from flask_wtf.csrf import CSRFProtect  # Protección CSRF en formularios POST.

db = SQLAlchemy()  # Instancia ORM global.
login_manager = LoginManager()  # Auth.
socketio = SocketIO(cors_allowed_origins="*")  # Chat tiempo real.
csrf = CSRFProtect()  # Tokens CSRF.
migrate = Migrate()  # alembic init/migrate.
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])  # Límite global suave.
