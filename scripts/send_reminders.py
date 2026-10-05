# =============================================================================
# scripts/send_reminders.py — Recordatorios WhatsApp/email 24 h antes de la cita
# =============================================================================
# Uso:
#   python scripts/send_reminders.py             # envía y marca como enviado
#   python scripts/send_reminders.py --dry-run   # solo muestra lo que se enviaría
#
# Se ejecuta diario (07:00 en Managua) desde .github/workflows/reminders.yml.
# Con Twilio configurado (TWILIO_*) el WhatsApp se envía solo; sin Twilio se
# registra el deep-link wa.me en logs para no perder el recordatorio.

import argparse
import sys

from app import app as flask_app
from reminders import send_pending


def main(dry_run: bool = False) -> int:
    with flask_app.app_context():
        result = send_pending(dry_run=dry_run)
    if dry_run:
        print(f"[DRY-RUN] {result['pending']} recordatorio(s) para {result['target']}.")
        return 0
    print(
        f"Listo: {result['sent']} enviados, {result['failed']} fallidos, "
        f"{result['pending']} en cola ({result['target']})."
    )
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recordatorios de citas 24 h antes")
    parser.add_argument("--dry-run", action="store_true", help="No envía, solo imprime")
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
