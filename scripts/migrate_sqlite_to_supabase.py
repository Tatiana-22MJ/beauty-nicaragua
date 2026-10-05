# =============================================================================
# migrate_sqlite_to_supabase.py — Migra datos de SQLite local a Supabase
# =============================================================================
# Uso:
#   1) NO definas DATABASE_URL en el entorno (para leer el SQLite local
#      instance/beauty.db) y define el destino:
#         TARGET_DATABASE_URL="postgresql://postgres.<ref>:<pass>@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
#   2) Ejecuta:
#         python scripts/migrate_sqlite_to_supabase.py             # migrar
#         python scripts/migrate_sqlite_to_supabase.py --dry-run   # solo contar
#
# - Crea el esquema en el destino (create_all) si no existe.
# - Copia las filas preservando los IDs.
# - Reajusta las secuencias serial en Postgres para no romper nuevos INSERT.
# - Aborta si el destino ya tiene usuarios (evita duplicar), salvo --force.
# =============================================================================

import os
import sys

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config  # noqa: E402
from extensions import db  # noqa: E402
from models import (  # noqa: E402
    AuditLog,
    Booking,
    ChatMessage,
    SalonInfo,
    Service,
    ServicePackage,
    User,
)

# Orden respetando dependencias FK.
TABLES = [User, Service, ServicePackage, Booking, ChatMessage, SalonInfo, AuditLog]


def normalize_target_url(raw: str) -> str:
    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql://", 1)
    if raw.startswith("postgresql://"):
        raw = raw.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw


def row_dict(obj):
    return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv

    target_url = os.environ.get("TARGET_DATABASE_URL", "")
    if not target_url:
        print("ERROR: define TARGET_DATABASE_URL (cadena del pooler de Supabase).")
        return 1
    target_url = normalize_target_url(target_url)

    # Import diferido: la app fuente se crea con el DATABASE_URL del entorno
    # (por defecto, el SQLite local). No setees DATABASE_URL para este script.
    from app import create_app  # noqa: E402

    source_app = create_app()
    if not source_app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        print("ERROR: el origen debe ser el SQLite local. NO definas DATABASE_URL al ejecutar este script.")
        return 1

    engine = create_engine(target_url, pool_pre_ping=True)
    TargetSession = sessionmaker(bind=engine)

    with source_app.app_context():
        with engine.connect() as conn:
            existing = inspect(conn)
            if "users" in existing.get_table_names():
                n = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                if n and not force:
                    print(f"El destino ya tiene {n} usuarios. Abortando (usa --force para continuar).")
                    return 1

        print("== Conteo en origen (SQLite) ==")
        for model in TABLES:
            print(f"  {model.__tablename__:>18}: {model.query.count()}")

        if dry_run:
            print("\n--dry-run: no se escribió nada. Quita --dry-run para migrar.")
            return 0

        # Esquema en destino (idempotente con checkfirst).
        db.metadata.create_all(engine)

        target = TargetSession()
        try:
            for model in TABLES:
                rows = model.query.all()
                for obj in rows:
                    target.add(model(**row_dict(obj)))
                target.commit()
                print(f"  {model.__tablename__:>18}: {len(rows)} filas migradas.")

            # Reajustar secuencias (Postgres) para nuevos INSERT sin colisión de PK.
            for model in TABLES:
                table = model.__tablename__
                try:
                    target.execute(
                        text(
                            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                            f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
                        )
                    )
                    target.commit()
                except Exception:
                    target.rollback()  # SQLite u otra BD sin secuencias.

            print("\n✔ Migración completada. Siguiente paso: apunta DATABASE_URL al pooler de Supabase.")
            return 0
        except Exception:
            target.rollback()
            raise
        finally:
            target.close()


if __name__ == "__main__":
    raise SystemExit(main())
