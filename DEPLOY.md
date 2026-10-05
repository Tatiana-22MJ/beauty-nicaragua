# Deploy — Beauty Nicaragua

Guía de despliegue en **Railway** + los dos GitHub Actions (recordatorios y backups).

## 1. Railway

1. [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo** →
   `Tatiana-22MJ/beauty-nicaragua`.
2. Railway detecta `railway.json` (builder Dockerfile, healthcheck `/healthz`,
   restart `ON_FAILURE`). El contenedor escucha en `$PORT` (inyectado por Railway;
   en local cae a 5000).
3. En **Variables**, define (copiar de `.env.example`):

   | Variable | Valor |
   |---|---|
   | `FLASK_ENV` | `production` (activa fail-fast de secretos) |
   | `SECRET_KEY` | 64 hex aleatorios: `python -c "import secrets;print(secrets.token_hex(32))"` |
   | `ADMIN_PASSWORD` | fuerte (si queda `Admin123!` la app **no arranca**) |
   | `DATABASE_URL` | rol **`beauty_app`** del pooler (`SUPABASE_SETUP.md` §9) |
   | `SUPABASE_URL` | `https://<ref>.supabase.co` |
   | `SUPABASE_SECRET_KEY` | `sb_secret_…` |
   | `SUPABASE_BUCKET_PROOFS` | `payment-proofs` |
   | `SESSION_COOKIE_SECURE` | `1` |
   | `TRUST_PROXY_HEADERS` | `1` |
   | `LOG_FORMAT` | `json` |
   | `SENTRY_DSN` | opcional |
   | `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_WHATSAPP_FROM` | opcional (sin ellos se loguea el link `wa.me`) |
   | `MAIL_ENABLED` / `MAIL_SERVER` / `MAIL_USERNAME` / `MAIL_PASSWORD` / `MAIL_DEFAULT_SENDER` | opcional |

   > **No** pongas `BACKUP_DATABASE_URL` (rol `postgres`) en la app.

4. **Deploy**. Al arrancar: `alembic upgrade` (+ reintento ante carrera de 2
   workers) → seeds → `GET /healthz` debe devolver `{"status":"ok"}`.
5. `RATELIMIT_STORAGE_URI`: con un solo worker sirve `memory://`; si escalas a
   varios workers, añade el plugin Redis de Railway y usa `redis://…`.

### Verificación posterior

```bash
curl https://<tu-app>.up.railway.app/healthz
```

- `/` carga, `/login` funciona con el admin.
- Reserva de prueba + comprobante → aparece en `/admin/citas`.
- `/admin/resenas` y `/admin/clientas` responden (solo admin).

## 2. GitHub Actions secrets

**Settings → Secrets and variables → Actions → New repository secret**

| Secret | Workflow | Valor |
|---|---|---|
| `DATABASE_URL` | `reminders.yml` | rol `beauty_app` (mismo que la app) |
| `BACKUP_DATABASE_URL` | `backup.yml` | rol `postgres` (§2 de `SUPABASE_SETUP.md`) |
| `SUPABASE_URL` | `backup.yml` | `https://<ref>.supabase.co` |
| `SUPABASE_SECRET_KEY` | `backup.yml` | `sb_secret_…` |
| `TWILIO_ACCOUNT_SID` | `reminders.yml` | SID de Twilio |
| `TWILIO_AUTH_TOKEN` | `reminders.yml` | token de Twilio |
| `TWILIO_WHATSAPP_FROM` | `reminders.yml` | p. ej. `whatsapp:+14155238886` (sandbox) o tu número |
| `MAIL_*` | `reminders.yml` | opcional (email de respaldo) |

## 3. Cronograma operativo (hora de Managua)

| Workflow | UTC | Managua | Qué hace |
|---|---|---|---|
| `ci.yml` | push/PR | — | flake8 (críticos) + pytest + cobertura |
| `reminders.yml` | `0 13 * * *` | 07:00 | WhatsApp/email a citas de mañana |
| `backup.yml` | `0 3 * * *` | 21:00 | `pg_dump` → Storage `backups/` + artifact 14 días |

Ambos cron aceptan **Run workflow** manual (`workflow_dispatch`) para probarlos.

## 4. Restaurar un backup

```bash
gunzip -c beauty-AAAA-MM-DD.sql.gz | psql "$BACKUP_DATABASE_URL"
```

O desde el SQL Editor de Supabase: pegar el `.sql` descomprimido.

## 5. Rollback

- Railway: pestaña **Deployments → Redeploy to previous deploy**.
- BD: Alembic (`flask db downgrade -1`) o restore del backup (§4).
