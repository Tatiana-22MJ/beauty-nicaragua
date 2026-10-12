# Sesión 12/10/2026 — Revisión con las skills + arreglos de seguridad

## Qué hicimos

Primero revisamos todo el proyecto con las 13 skills del proyecto
(los checklists de seguridad, pruebas, base de datos, web de belleza, etc.).
Después aplicamos los arreglos más importantes, en modo guiado.

### Arreglos aplicados

| Archivo | Qué cambió | Por qué |
|---|---|---|
| `tests/conftest.py` | Vaciamos las credenciales de Twilio y email en los tests | Un test jamás debe enviar mensajes de verdad a teléfonos o correos reales |
| `Dockerfile` | `ENV FLASK_ENV=production` | Si alguien olvida la variable en Railway, la app queda en modo seguro por defecto |
| `notifications.py`, `reminders.py` | Los logs ya no guardan nombres, teléfonos ni cuerpos de mensajes | Los logs son datos sensibles: si alguien los filtra, no debe ver los datos de las clientas |
| `routes_admin.py` | Función `_csv_cell` que neutraliza `=`, `+`, `-`, `@` al inicio de una celda | CSV injection: una clienta podría escribir una fórmula de Excel en su nombre y, al abrir la dueña el archivo, se ejecutaría |
| `config.py` | Constantes `CANCELLATION_HOURS=24`, `LATE_TOLERANCE_MINUTES=30`, `NO_SHOW_FORGIVEN=1` | Las políticas las define la dueña y viven en un solo lugar, no escondidas en el HTML |
| `app.py` | Context processor inyecta `deposit_percent` y `policy`; `/reservar` exige la casilla `accept_policies` | El servidor siempre valida, aunque el HTML ya marque `required` (el HTML lo puede saltar cualquiera) |
| `templates/index.html`, `static/css/style.css` | Sección de políticas visibles antes de reservar + casilla de aceptación | Regla del formato web de belleza: las políticas se muestran ANTES de pagar |
| `templates/legal/terms.html` | Políticas reales (decía que el anticipo era "opcional") | El texto contradecía al formulario |
| `.github/workflows/ci.yml`, `requirements-dev.txt` | `pip-audit` en el CI | Detecta dependencias con vulnerabilidades conocidas (CVE) |
| `.gitignore` | `.opencode/` y `supabase/.temp/` | Para que no se cuelen en un commit por error |
| `TESTING_GUIDE.md`, `docs/IMPLEMENTACION_COMPLETA.md` | Fuera la contraseña `Admin123!` publicada | Una credencial en un repo público es una puerta abierta |
| `PENDIENTES.md` | Verificado que los crons ya están desactivados en `main`; añadida la práctica diferida y las siguientes sesiones | Documentación al día |

### Resultados

- **90 pruebas pasan** (88 de antes + 2 nuevas de la casilla de políticas).
- flake8 sin avisos nuevos (quedan 3 E501 preexistentes = ejercicio práctico).
- **No se quitó ninguna función de la web.**
- El `pip-audit` del CI encontró **17 CVEs en 4 paquetes** (Flask, Werkzeug,
  requests, python-dotenv); se actualizaron los pins a las versiones corregidas
  (commit `1d3b9f4`) y la auditoría quedó limpia. Ejemplo real de por qué
  vale la pena auditar dependencias.

## Conceptos nuevos de esta sesión

- **Variable de entorno (*env var*)**: clave-valor fuera del código, en el servidor.
  Como una caja fuerte aparte del edificio: el código entra sin verla.
- **Fail-safe / seguro por defecto**: si falta un dato, que la app caiga en la
  opción **segura**, no en la peligrosa (`FLASK_ENV=production` en el Dockerfile).
- **Mock**: una imitación que responde "sí" sin hacer la acción real
  (los tests usan mock de Twilio/email para no enviar nada).
- **CSV injection**: fórmulas de Excel escondidas en datos de usuarias;
  el antídoto es anteponer `'` (truco estándar OWASP).
- **Defensa en profundidad**: repetir la misma protección en varios capas
  (casilla `required` en HTML **y** validación en el servidor).
- **CVE**: lista pública de fallos de seguridad con nombre y número
  (ej. `CVE-2026-102598`); `pip-audit` las busca en tus dependencias.
- **Context processor** (Flask): función que mete variables en todas las
  plantillas para no repetirlas (`deposit_percent`, `policy`).

## Preguntas de comprobación ( responder en la próxima sesión )

1. ¿Por qué los tests no deben tener la contraseña real de Twilio?
2. Si Railway pierde `FLASK_ENV`, ¿qué protege la app ahora?
3. El HTML ya marca la casilla `required`; ¿para qué validarla también en `app.py`?

## Pregunta de entrevista de esta sesión

**P: "¿Cómo evitas que un atacante robe datos por los logs?"**
**R:** "Los logs solo guardan identificadores; los nombres, teléfonos y mensajes
de las clientas se omiten, porque los logs también son datos sensibles."

## Lo que Tatiana ya domina

- Estructura del proyecto y la agenda (slots, duraciones, doble reserva).
- HTML y CSS; leer mensajes de error y localizar la línea.

## Lo que queda por practicar (ver `PENDIENTES.md`)

- Test IDOR (clienta A no abre la cita de la clienta B) con `TODO`.
- Decorador `@role_required` con huecos.
- Migración de índices (`bookings.user_id`, `status`) con guía.
- Arreglar 3 avisos de flake8 a mano.
