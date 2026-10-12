# Pendientes

Lista de tareas pendientes del proyecto beauty-nicaragua.

## GitHub Actions

- [x] Desactivar los disparos automáticos (`schedule:`) que fallaban a diario en `main` (12/10/2026):
  - [x] `.github/workflows/backup.yml` — «Backup diario de Postgres (Supabase)»
  - [x] `.github/workflows/reminders.yml` — «Recordatorios WhatsApp/email (24 h antes)»
  - Estado: `schedule:` comentado en ambos; queda `workflow_dispatch` (ejecución manual). **Falta subir el cambio a `main`** para que GitHub deje de lanzarlos.
- [ ] Investigar por qué fallaban y reactivarlos otro día:
  - Backup: revisar secrets `BACKUP_DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`.
  - Recordatorios: revisar secrets de Twilio y `MAIL_*`, y el script `scripts/send_reminders.py`.
  - Para reactivar: descomentar el `schedule:` en cada YAML y subir a `main` (Skill 10 · Despliegue y operaciones).
