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
| `DATABASE_URL` | rol **`beauty_app`** (permisos mínimos), no `postgres` (ver §9) |

Backups: ver §10 (GitHub Action con `pg_dump` diario → Storage + artifact).

## 8. Fase 2 (opcional, más adelante)

- **Supabase Auth**: reset de contraseña managed, magic links, Google OAuth.
- **Realtime**: sustituir Flask-SocketIO en el chat.
- **Edge Functions + pg_cron**: recordatorios WhatsApp programados sin servidor.

## 9. Rol de BD de mínimos privilegios (`beauty_app`)

La app **no** debe conectarse como `postgres`. El rol dedicado ya existe y es el
que usa `DATABASE_URL` en `.env`:

```sql
create role beauty_app with login password '<clave_fuerte>';
grant usage, create on schema public to beauty_app;
grant select, insert, update, delete on all tables in schema public to beauty_app;
grant usage, select on all sequences in schema public to beauty_app;
alter default privileges for role postgres in schema public
    grant select, insert, update, delete on tables to beauty_app;
alter default privileges for role postgres in schema public
    grant usage, select on sequences to beauty_app;
```

- En el **pooler** el tenant va en el usuario: `beauty_app.ndlvhagcilnyffuyfvbf@…pooler.supabase.com:5432`.
- **RLS queda habilitada** en las 8 tablas y se crea una policy exclusiva por
  tabla (`app_all … to beauty_app`, `using (true) with check (true)`) — el bloque
  `do $$ … $$` al final de `supabase/schema.sql` la aplica. La Data API pública
  (`anon`/`authenticated`) sigue sin ningún grant: no puede leer ni escribir.
- `postgres` en Supabase **no es superuser**, por eso los `alter default privileges
  for role beauty_app` se ejecutan *como* `beauty_app` (son sus propios defaults).
- Rotar la clave: `alter role beauty_app with password '<nueva>';` y actualizar `.env`.

## 10. Backups diarios

Workflow `.github/workflows/backup.yml` (cron 03:00 UTC = 21:00 Managua):

1. `pg_dump` con la imagen `postgres:17-alpine` (misma versión mayor que Supabase).
2. Sube el `.sql.gz` al bucket privado **`backups`** de Supabase Storage.
3. Conserva el artifact del runner por 14 días.

Secrets de GitHub requeridos:

| Secret | Valor |
|---|---|
| `BACKUP_DATABASE_URL` | URL del rol `postgres` (§2). **No** la de la app. |
| `SUPABASE_URL` | `https://<ref>.supabase.co` |
| `SUPABASE_SECRET_KEY` | `sb_secret_…` (Service Role, nunca la `anon`) |

Restaurar: `gunzip -c backup-FECHA.sql.gz | psql "$BACKUP_DATABASE_URL"`.
