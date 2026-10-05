# Plan de Mejoras — Beauty Nicaragua

> Auditoría técnica + investigación de mercado (salones en Nicaragua) + plan de integración con **Supabase**.
> Fecha: octubre 2026 · Stack actual: Flask 3 + SQLAlchemy + Flask-Login + Flask-SocketIO + SQLite

> ## ✅ ESTADO (octubre 2026): P0 y Supabase Fase 1 IMPLEMENTADOS
>
> Verificado con **61 tests pytest (100% pass)** + flake8 limpio + arranque verificado.
>
> | # | Mejora | Estado |
> |---|--------|--------|
> | 1 | Fail-fast de credenciales en producción (`validate_production`) | ✅ `config.py` |
> | 2 | Seed ya no borra datos del admin (flag `is_seed` + FK-safe) | ✅ `models.py` + `seeds.py` |
> | 3 | Anti doble-reserva: índice único parcial + catch `IntegrityError` → 409 | ✅ `models.py`, `app.py`, `routes_account.py` |
> | 4 | Rate limiter global con Redis (env `RATELIMIT_STORAGE_URI`) | ✅ config + `.env.example` |
> | 5 | SocketIO sin CORS comodín + `gthread` en Procfile | ✅ `extensions.py`, `app.py`, `Procfile` |
> | 6 | Comprobantes: firma real (magic bytes) + **Supabase Storage** con fallback local | ✅ `validators.py`, `supabase_storage.py` |
> | 7 | Reset de contraseña completo (tokens firmados 1 h) | ✅ `app.py` + templates |
> | 8 | Admin: parsing seguro (sin 500s) + ver comprobante (URL firmada / local) | ✅ `routes_admin.py` |
> | 9 | `ProxyFix` + security headers + HSTS | ✅ `app.py` |
> | 10 | Stack actualizado: Flask 3.1, psycopg3, sin eventlet | ✅ `requirements.txt` |
> | 12/14 | Timezone `America/Managua` en toda la agenda | ✅ `timeutils.py` |
> | — | Ruta faltante `account.booking_detail` (rompía Mi cuenta) | ✅ `routes_account.py` |
> | 21 | Suite de tests: 61 tests (validadores, agenda, auth, reservas, reset) | ✅ `tests/` |
> | — | Guía de conexión + schema.sql + script de migración SQLite→Supabase | ✅ `SUPABASE_SETUP.md` |
>
> **Pendiente (P1/P2):** recordatorios WhatsApp automáticos, slots por duración, link de pago, reseñas, CSV export.

---

## 1. Diagnóstico rápido

Lo que ya está bien (mantener):

- Arquitectura por blueprints + factory pattern, separación limpia (models / validators / availability / notifications).
- CSRF, rate limiting, validación doble cliente/servidor, escape XSS en el chat.
- Localización seria: NIO, +505, `America/Managua`, schema.org, catálogo alineado al mercado.
- Flujo de negocio real: anticipo por transferencia + comprobante + auditoría admin.

Lo que hay que corregir: credenciales por defecto, un bug que borra datos del admin, race condition en la agenda, dependencias viejas, y cero tests.

---

## 2. P0 — Críticos (seguridad / bugs que pierden datos)

| # | Problema | Detalle | Solución |
|---|----------|---------|----------|
| 1 | **Credenciales por defecto** | `SECRET_KEY` tiene valor hardcodeado y `ADMIN_PASSWORD` default `Admin123!`. Si se despliega sin env vars, cualquiera entra al panel admin. | En `ProductionConfig`, lanzar excepción al arrancar si `SECRET_KEY`/`ADMIN_PASSWORD` siguen en default. Rotar la clave actual. |
| 2 | **`seed_database()` borra servicios creados por el admin** | Cada arranque elimina todo `Service`/`ServicePackage` cuyo nombre no esté en el seed. El trabajo hecho desde `/admin/servicios` **se pierde al reiniciar**. | Añadir columna `is_seed BOOLEAN` y solo tocar registros con `is_seed=True`; nunca borrar lo creado desde el panel. |
| 3 | **Doble reserva (race condition)** | `is_slot_free()` → INSERT no es atómico. Dos peticiones simultáneas reservan el mismo hueco. | Índice único parcial en `(preferred_date, preferred_time)` para estados activos + capturar `IntegrityError` → 409 "horario ocupado". |
| 4 | **Rate limiter en memoria** | `RATELIMIT_STORAGE_URI=memory://` no funciona con los 3 workers de gunicorn del Dockerfile: cada worker cuenta por separado y se reinicia al redeploy. | Redis: `RATELIMIT_STORAGE_URI=redis://...` (mismo Redis sirve para sesiones y SocketIO). |
| 5 | **SocketIO abierto** | `cors_allowed_origins="*"` y `allow_unsafe_werkzeug=True` en `__main__`. | Restringir origins a tu dominio; en prod correr gunicorn con `--worker-class gthread` (coherente con `async_mode="threading"`). |
| 6 | **Uploads: solo extensión + disco local** | `_allowed_proof()` valida extensión, no MIME real; y `instance/uploads` se pierde en deploys efímeros (Heroku/Railway/Docker). | Verificar magic bytes (`python-magic`), y migrar comprobantes a **Supabase Storage** (bucket privado + URLs firmadas). |
| 7 | **Admin: parsing sin try/except** | `float(request.form.get("price") or 0)` en `routes_admin.py` → 500 con input no numérico. | Validar con `validators.py` y devolver flash + redirect, no 500. |
| 8 | **Sin `ProxyFix`** | Detrás de Nginx/proxy, `request.remote_addr` es la IP del proxy → rate limiting agrupa a todos; cookies seguras fallan. | `ProxyFix(app.wsgi_app, x_for=1, x_proto=1)` cuando `SESSION_COOKIE_SECURE=1`. |
| 9 | **Dependencias viejas / eventlet** | Flask 2.3.3 (2023), `eventlet` deprecado con CVEs conocidos y además **no se usa** (`async_mode="threading"`). | Subir a Flask 3.x + SQLAlchemy 2.x, eliminar `eventlet`, pin de seguridad (`pip-audit` en CI). |
| 10 | **Sin reset de contraseña ni verificación de email** | La clienta que olvida su clave no puede recuperar la cuenta. | **Supabase Auth** lo resuelve gratis (ver §4) o flujo SMTP propio con tokens firmados. |

## 3. P1 — Producto (mercado Nicaragua)

| # | Mejora | Por qué (contexto NI) |
|---|--------|----------------------|
| 11 | **Recordatorios automáticos WhatsApp 24 h antes** | WhatsApp es el canal dominante en Nicaragua; los recordatorios reducen no-shows (la herramienta #1 de Fresha/Booksy/Zenoti). Hoy solo envías email + link manual. Cron diario: citas de mañana → `wa.me` a la clienta. |
| 12 | **Slots conscientes de duración** | La agenda trata todo como 60 min: un balayage de 120 min se puede agendar a las 17:00 (cierra 18:00) y un servicio de 45 min bloquea un hueco completo. Generar slots según `duration_minutes` y bloquear tiempo real. |
| 13 | **Pagos: mantener transferencia + añadir link/QR** | Cultura NI: transferencia/QR + WhatsApp. Opciones investigadas: **BAC Credomatic** (e-commerce 3D Secure + NIC Click to Pay), **LAFISE** (adquirencia + Poket QR), agregadores **Recurrente** / **Pagadito** (API simple, links de pago), PayPal solo para clientes del exterior. Fase 1: link de pago generado en la confirmación. Fase 2: webhook que marca `payment_status=paid` automático. |
| 14 | **Timezone real (America/Managua)** | `validate_date` y `available_slots` usan la hora del servidor. Usar `zoneinfo.ZoneInfo("America/Managua")` en todo el cálculo de agenda. |
| 15 | **Notificaciones en background** | SMTP/Twilio bloquean hasta 20 s dentro del request de reserva. Thread con cola o RQ/Celery; Supabase Edge Functions + pg_cron como alternativa sin servidor. |
| 16 | **Perfil de clienta + historial** | Los líderes (Fresha, Booksy) guardan historial de servicios, notas de la estilista y gasto acumulado. Ya tienes `bookings` por usuario: agregar vista "ficha de clienta" en admin. |
| 17 | **Reseñas post-cita** | Al marcar cita `completed`, pedir reseña (WhatsApp/email) y publicar testimonios verificados → SEO local. |
| 18 | **SEO local** | Google Business Profile (imprescindible en Managua), sitemap.xml, robots.txt, OG images por página, horarios en schema.org `openingHours`. |
| 19 | **Admin: paginación + export CSV** | `/admin/citas` limita a 100 sin paginar. Añadir paginación y export CSV de citas/pagos (contabilidad). |
| 20 | **Modelo de personal** | La agenda asume 1 silla. Si hay varias estilistas, modelo `Staff` + `Booking.staff_id` (los sistemas líderes lo tienen core). Puede esperar a validar demanda. |

## 4. Supabase — plan de integración

### Fase 1 (recomendada, ~1–2 días): Supabase como Postgres + Storage

Mantén Flask, SQLAlchemy y Flask-Login (migración de bajo riesgo); Supabase entra como infraestructura.

1. **Crear proyecto** en región `us-east-1` (N. Virginia — menor latencia hacia Managua).
2. **Conexión**: usar el **pooler Supavisor en modo sesión (puerto 5432)**, ideal para workers gunicorn de larga vida:
   ```bash
   DATABASE_URL="postgresql://postgres.<ref>:<password>@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
   ```
   - `pip install psycopg[binary] supabase`
   - Engine: `pool_pre_ping=True, pool_size=10, max_overflow=5`.
   - (Si algún día usas modo transacción, puerto 6543, hay que desactivar prepared statements: psycopg3 `prepare_threshold=None`.)
3. **Storage para comprobantes**: bucket privado `payment-proofs`. El backend sube con `service_role` key (**solo server-side, nunca en el frontend**) y el admin visualiza con URLs firmadas. Elimina la dependencia de disco local (resuelve P0 #6).
4. **Migración de datos**: script pequeño SQLite→Postgres (o `pgloader`); luego correr `seeds.py` una vez.
5. **Migraciones serias**: adoptar Alembic (ya tienes Flask-Migrate instalado y sin usar) como única fuente de verdad y **eliminar `migrate_schema()`** con sus ALTERs raw.
6. **RLS**: como solo el backend toca la BD con un rol dedicado, crea un rol `beauty_app` con permisos mínimos (ni `postgres` ni exposición de la Data API). Si expones la Data API, habilita RLS en **todas** las tablas antes.
7. **Backups**: free tier no incluye; programar `pg_dump` (GitHub Action cron) o plan Pro.
8. Retirar el servicio `db` de docker-compose (Supabase lo sustituye).

### Fase 2 (opcional, por módulo)

| Módulo Supabase | Qué reemplaza | Esfuerzo |
|-----------------|---------------|----------|
| **Auth** | Flask-Login: reset de contraseña, verificación email, magic links, Google OAuth | Medio (sesión pasa a JWT; validar en Flask) |
| **Realtime** | Flask-SocketIO en el chat (menos infra que escalar) | Medio |
| **Edge Functions + pg_cron** | Cron de recordatorios WhatsApp sin servidor propio | Bajo |
| **Webhooks/Funcs** | Confirmación de pago automática desde pasarela | Bajo |

> Recomendación: Fase 1 completa antes de tocar Auth. La Fase 2 solo si el bootstrapping de Auth propio (P0 #10) se vuelve costoso.

---

## 5. P2 — Calidad técnica

| # | Mejora | Nota |
|---|--------|------|
| 21 | **Tests (bloqueante para CI)** | El workflow corre `pytest` pero **no existe ni un test**. Añadir: pytest + fixtures de app en memoria, tests de validators/availability/slots, 1 test E2E Playwright del flujo reserva. |
| 22 | **`Booking.preferred_date` como `Date`, no `String`** | Comparaciones e índices correctos; habilita el índice único del P0 #3. |
| 23 | **PDF real** | El generador manual es latin-1 (sin acentos: "Comprobante" OK pero "Días" no), 1 página fija. Usar `fpdf2`. |
| 24 | **Imágenes WebP + lazy loading** | Los PNG de servicios pesan; `loading="lazy"` y WebP → mejora LCP en móviles (mayoría del tráfico NI es móvil). |
| 25 | **Three.js r128 (2021) desactualizado** | Actualizar a r160+ o degradar a canvas 2D/CSS en móviles de gama baja; lazy-load del módulo 3D. |
| 26 | **Observabilidad** | Endpoint `/healthz`, Sentry (free tier), logging JSON estructurado. |
| 27 | **Higiene de repo** | `git rm --cached server.log compile.log` (ya están en .gitignore pero trackeados); borrar `Pasted Image` del repo. |
| 28 | **Límite de vida de sesión** | `PERMANENT_SESSION_LIFETIME` explícito + rotación de `REMEMBER_COOKIE`. |

---

## 6. Referencias de la investigación

**Proyectos/sistemas similares analizados:** Fresha, Booksy, Vagaro, Mindbody, Zenoti, SimplyBook.me, Setmore, Reservio, OpenSalon (open source). Features comunes del rubro: disponibilidad en tiempo real, depósitos anti no-show, recordatorios automáticos (SMS/WhatsApp), ficha e historial de clienta, calendarios por estilista, packs/membresías, POS, reseñas, campañas de marketing, reportes. Nuestro gap principal: recordatorios automáticos, duración real por servicio y ficha de clienta.

**Pagos Nicaragua (2026):** BAC Credomatic e-commerce (3D Secure, NIC Click to Pay), LAFISE adquirencia + Poket (QR), Recurrente y Pagadito (agregadores CA con API/links de pago), PayPal (solo exterior). Cultura dominante: transferencia + WhatsApp → mantener el flujo manual como fallback, no como único camino.

**Supabase:** quickstart oficial Flask (supabase-py), docs de conexión (Supavisor: 5432 sesión / 6543 transacción), guía SQLAlchemy+Supabase. Region recomendada: us-east-1.

---

## 7. Orden de ejecución sugerido

1. **Semana 1 (P0):** #1, #2, #3, #4, #9, #10 parcial (tokens reset propios) + #21 (tests mínimos que cubran lo cambiado).
2. **Semana 2 (Supabase Fase 1):** conexión Postgres + Storage de comprobantes + Alembic + backups. Retirar docker-db.
3. **Semana 3–4 (P1):** #11 recordatorios WhatsApp, #12 duración por servicio, #14 timezone, #13 link de pago (Recurrente o BAC).
4. **Después:** Fase 2 de Supabase por módulo y P2.
