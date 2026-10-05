# Conectar Beauty Nicaragua a Supabase

Guía de integración **Fase 1**: Supabase como Postgres + Storage de comprobantes.
Flask, SQLAlchemy y Flask-Login siguen igual — migración de bajo riesgo (~1 h).

---

## 1. Crear el proyecto

1. Ve a [database.new](https://database.new) y crea un proyecto (plan Free sirve para empezar).
2. **Región:** `us-east-1` (N. Virginia) — la de menor latencia hacia Managua.
3. Guarda la contraseña de la BD: la necesitas para la cadena de conexión.

## 2. Conectar la base de datos (pooler Supavisor)

Dashboard → **Connect** → pestaña **Session pooler** (puerto **5432**, ideal para
workers gunicorn de larga vida). Copia la cadena y ponla en `.env`:

```bash
DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

> **Nota técnica:** la app reescribe la URI a `postgresql+psycopg://` automáticamente
> (psycopg3, ya en requirements). `pool_pre_ping` + `pool_size=10` se activan solos.
> No uses el puerto 6543 (modo transacción) con esta app: requiere desactivar
> prepared statements.

## 3. Crear el esquema

Dos opciones (elige UNA):

- **Opción A (recomendada):** Dashboard → **SQL Editor** → pega `supabase/schema.sql` → Run.
  Crea tablas, índices y RLS.
- **Opción B:** deja que la app cree las tablas con `db.create_all()` al arrancar
  (RLS quedará deshabilitado; ejecuta al menos la sección RLS del schema.sql después).

## 4. Migrar tus datos locales (opcional)

Si tu `instance/beauty.db` ya tiene usuarias, citas o chats:

```bash
# 1) Sin DATABASE_URL en el entorno (origen = SQLite local)
# 2) Apunta al destino:
set TARGET_DATABASE_URL=postgresql://postgres.<ref>:<pass>@aws-0-us-east-1.pooler.supabase.com:5432/postgres

python scripts/migrate_sqlite_to_supabase.py --dry-run   # verificar conteos
python scripts/migrate_sqlite_to_supabase.py             # migrar
```

El script preserva IDs y reajusta las secuencias `serial`.

## 5. Storage de comprobantes (Supabase Storage)

1. Dashboard → **Settings → API Keys**: copia `Project URL` y la **Secret key**
   (formato nuevo `sb_secret_...`; si tu proyecto usa el formato legacy, es la
   `service_role`). El publishable key (`sb_publishable_...`) NO sirve para el
   backend — es pública.
2. En `.env`:
   ```bash
   SUPABASE_URL=https://<ref>.supabase.co
   SUPABASE_SECRET_KEY=sb_secret_...
   SUPABASE_BUCKET_PROOFS=payment-proofs
   ```
3. Listo: la app **crea el bucket privado automáticamente** al subir el primer
   comprobante. Los admins lo visualizan con URLs firmadas (1 h) desde
   `/admin/citas → 📎 Ver comprobante`.

> ⚠️ La `service_role` **solo vive en el backend** (variables de entorno del
> servidor). Nunca la pongas en el frontend ni la subas al repo.

Sin esas variables la app sigue funcionando con disco local (desarrollo).

## 6. Arrancar y verificar

```bash
py -m pip install -r requirements.txt
py app.py
```

Checklist:

- [ ] `GET /` carga servicios con precios C$
- [ ] Login admin (tus credenciales de `ADMIN_USERNAME`/`ADMIN_PASSWORD`)
- [ ] Reservar una cita → aparece en `/mi-cuenta`
- [ ] Subir comprobante → visible en `/admin/citas → 📎 Ver comprobante`
- [ ] En Supabase → Table Editor: las filas aparecen en `bookings`

## 7. Producción (checklist senior)

| Variable | Valor |
|---|---|
| `FLASK_ENV` | `production` (activa `ProductionConfig` + fail-fast de secretos) |
| `SECRET_KEY` | aleatoria de 64 hex (si queda la de dev, la app **no arranca**) |
| `ADMIN_PASSWORD` | fuerte (idem) |
| `SESSION_COOKIE_SECURE` | `1` |
| `TRUST_PROXY_HEADERS` | `1` (detrás de proxy) |
| `RATELIMIT_STORAGE_URI` | `redis://...` (con >1 worker de gunicorn) |

Backups: el plan Free de Supabase no incluye backups automáticos — programa
`pg_dump` (Dashboard → Database → Backups en planes Pro) o un GitHub Action cron.

## 8. Fase 2 (opcional, más adelante)

- **Supabase Auth**: reset de contraseña managed, magic links, Google OAuth.
- **Realtime**: sustituir Flask-SocketIO en el chat.
- **Edge Functions + pg_cron**: recordatorios WhatsApp programados sin servidor.
