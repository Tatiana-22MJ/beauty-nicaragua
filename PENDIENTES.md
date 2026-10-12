# Pendientes

Lista de tareas pendientes del proyecto beauty-nicaragua.

## GitHub Actions

- [x] Desactivar los disparos automáticos (`schedule:`) que fallaban a diario en `main` (12/10/2026):
  - [x] `.github/workflows/backup.yml` — «Backup diario de Postgres (Supabase)»
  - [x] `.github/workflows/reminders.yml` — «Recordatorios WhatsApp/email (24 h antes)»
  - Estado: `schedule:` comentado en ambos; queda `workflow_dispatch` (ejecución manual).
  - Verificado (12/10/2026): el commit `29d2702` **ya está en `origin/main`**; GitHub ya no lanza los crons.
- [ ] Investigar por qué fallaban y reactivarlos otro día:
  - Backup: revisar secrets `BACKUP_DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`.
  - Recordatorios: revisar secrets de Twilio y `MAIL_*`, y el script `scripts/send_reminders.py`.
  - Para reactivar: descomentar el `schedule:` en cada YAML y subir a `main` (Skill 10 · Despliegue y operaciones).
- [ ] Verificar el backup con una **restauración de prueba** (Skill 10).

## Práctica pendiente (ejercicios diferidos del 12/10/2026)

Para hacer en modo práctica, con esqueletos `TODO` que Tatiana completa:

- [ ] Test IDOR de la clienta: escribir el test de que la clienta A **no** puede abrir,
      cancelar ni reseñar la cita de la clienta B cambiando el número en la URL
      (`/mi-cuenta/cita/<id>`). Guión: crear dos usuarias con sus citas, intentar
      la B desde la sesión de la A, esperar 404.
- [ ] Completar el decorador `@role_required(...)` con huecos `TODO`
      (versión futura de `admin_required` que acepte varios roles).
- [ ] Crear la migración de índices de Alembic (`bookings.user_id`, `bookings.status`,
      `reviews.user_id`) con mi guía, probando `upgrade` y `downgrade` en local.
- [ ] Correr `flake8 . --max-line-length=120` y arreglar a mano 3 avisos
      (2× E501 de línea larga + 1× F401 de import sin usar).
- [ ] Ejercicio de seguridad con pip-audit (caso real del 12/10/2026):
      1. Correr `pip-audit -r requirements.txt` y leer la tabla de vulnerabilidades.
      2. Elegir una fila (por ejemplo `requests`), buscar la CVE y entender qué fallo explota (investigar una sola, sin prisa).
      3. Actualizar el pin en `requirements.txt` a la versión de la columna "Fix Versions".
      4. Instalar, correr `pytest` y volver a correr `pip-audit` hasta que diga "No known vulnerabilities found".
      5. Referencia: el commit `1d3b9f4` ya hizo esto con Flask/Werkzeug/requests/python-dotenv (17 CVEs).
- [ ] Preguntas de comprobación + mini ejercicio de mentoría sobre los cambios
      del 12/10/2026 (tests aislados, FLASK_ENV, CSV injection, casilla de políticas).

## Siguientes sesiones (orden por riesgo, de menor a mayor)

- [ ] Reserva sin cuenta: hoy `POST /reservar` exige login y el formulario
      pierde los datos; añadir aviso antes de enviar si no hay sesión.
- [ ] Ruta `/admin/auditoria` para consultar el `AuditLog`
      (la plantilla `templates/admin/audit_log.html` existe pero nadie la renderiza).
- [ ] Migración de índices en `bookings.user_id`, `bookings.status` y FKs
      ( Skill 3 · Base de datos; hacer en modo práctica, ver arriba).
- [ ] Columna `role` en `User` + `@role_required` + matriz rol-ruta documentada
      (Skill 8 · Roles y permisos; sustituye el `is_admin` booleano).
- [ ] Limpieza de repo con aprobación (Skill 12): imágenes duplicadas
      (~4,2 MB en `static/images/services/`), `static/js/script.js` sin uso,
      SVGs de `static/images/servicios/`, docs históricos de `docs/`.
- [ ] Precios `Float` → `Numeric` en la BD (dinero con decimales exactos).
- [ ] `phone` con restricción única + comprobación en el registro.
- [ ] Contraste de `--text-dim` en `style.css` (3,1:1; mínimo WCAG AA 4,5:1).
- [ ] `robots.txt` y `sitemap.xml` (SEO local).
- [ ] Sincronizar `README.md` y `DEPLOY.md` con el estado real
      (crons desactivados, Python 3.11, secciones de la portada).
