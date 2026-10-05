# 💅 Beauty Nicaragua — Plataforma SPA Profesional

**Estado**: v1.0 Producción-Ready | Localización: 🇳🇮 Nicaragua | Moneda: C$ NIO

---

## 🎯 Características Implementadas

### ✅ Operación del Negocio
- **Panel Admin** (`/admin`) — CRUD completo de servicios, packs, citas y chats
- **Dashboard de Citas** — Vista diaria, filtrada por estado, con confirmación/cancelación
- **Disponibilidad Real** — Calendario con horarios libres (sin doble booking)
- **Área de Clienta** (`/mi-cuenta`) — Historial de citas, reprogramación, cancelación
- **Sistema de Pagos** — Anticipo sugerido (30%), comprobante de transferencia, estado de pago

### 📬 Notificaciones Integradas
- **Email** — Confirmación de cita, cambios de estado, anticipo
- **WhatsApp** — Via Twilio (opcional) o deep links wa.me
- **Plantillas** — Localizadas en español (Nicaragua)

### 🔒 Seguridad Producción
- **CSRF Protection** — Tokens en todos los formularios POST
- **Rate Limiting** — Login (10/min), Chat (30/min), Reserva (10/min)
- **Cookies Seguras** — HttpOnly, Secure, SameSite=Lax
- **Session Management** — Flask-Login con remember-me
- **Auditoría** — Logs de todas las acciones admin
- **SECRET_KEY** — Debe cambiarse en producción (ver `.env.example`)

### 💼 Gestión de Servicios
- **CRUD de Servicios** — Nombre, precio NIO, duración, icono, imagen
- **Packs/Combos** — Combos tipo mercado (ej: Spa relax C$2,100)
- **"Consultar Precio"** — Flag para servicios con precio dinámico (láser)
- **Orden de Visualización** — sort_order en admin

### 💬 Chat Integrado
- **Chatbot** — Responde sobre servicios, horarios, precio
- **Restricción Auth** — Solo usuarios autenticados
- **Historial** — Admin puede ver todas las conversaciones
- **Real-time** — SocketIO para mensajes instantáneos

### 👥 Gestión de Usuarios
- **Registro/Login** — Email + Username, password hasheado con bcrypt
- **Admin Flag** — Aceso al panel administrativo
- **Perfil de Clienta** — Ver/editar nombre, email, teléfono

---

## 🚀 Inicio Rápido

### Desarrollo Local

```bash
# 1. Clonar y entrar
git clone <repo>
cd beauty

# 2. Crear venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate.ps1  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar .env
cp .env.example .env

# 5. Ejecutar
python app.py
```

**URL local**: http://localhost:5000

### Con Docker Compose

```bash
docker-compose up
# Accede a http://localhost:5000
# PostgreSQL: localhost:5432
```

---

## 📁 Estructura del Proyecto

```
beauty/
├── app.py                    # Factory Flask, rutas principales, SocketIO
├── models.py                 # ORM: User, Service, ServicePackage, Booking, ChatMessage, AuditLog
├── routes_admin.py           # Panel administrativo (servicios, citas, packs, chats)
├── routes_account.py         # Área de clienta (mis citas, reprogramación, pago)
├── notifications.py          # Email + WhatsApp (Twilio)
├── availability.py           # Generación de horarios libres
├── chatbot.py                # Respuestas automáticas
├── validators.py             # Validaciones de formularios
├── config.py                 # Configuración (dev/prod)
├── extensions.py             # Extensiones compartidas (db, csrf, limiter, socketio)
├── requirements.txt          # Dependencias Python
├── Dockerfile                # Build para Docker
├── docker-compose.yml        # Dev: app + PostgreSQL
├── Procfile                  # Deploy: Railway/Render/Heroku
├── .env.example              # Template de configuración
├── .github/workflows/ci.yml  # GitHub Actions (tests + linting)
├── static/                   # CSS, JS, imágenes
├── templates/                # Jinja2 templates
│   ├── auth/                 # Login, registro
│   ├── account/              # Mi cuenta, mis citas
│   ├── admin/                # Panel administrativo
│   ├── errors/               # 404, 500, etc
│   └── legal/                # Privacidad, términos
├── instance/                 # BD SQLite + uploads
├── seeds.py                  # Datos iniciales (servicios, admin user)
└── README.md                 # Este archivo
```

---

## 🔧 Configuración (Producción)

### 1. Variables de Entorno

Copia `.env.example` a `.env` y ajusta:

```bash
# Seguridad
SECRET_KEY=tu-clave-super-segura-de-128-caracteres

# Database (PostgreSQL en Railway/Render)
DATABASE_URL=postgresql://user:pass@host:5432/beauty

# Email (Sendgrid, Gmail, etc)
MAIL_ENABLED=1
MAIL_SERVER=smtp.sendgrid.net
MAIL_USERNAME=apikey
MAIL_PASSWORD=SG.xxx

# WhatsApp (Twilio, opcional)
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Admin seed
ADMIN_USERNAME=admin
ADMIN_PASSWORD=GeneraUnaContraseñaSegura123!
ADMIN_EMAIL=admin@beauty-nicaragua.com
```

### 2. Deploy a Railway/Render

#### Railway

1. Conecta repo a Railway
2. Agrega variables de `.env` en Settings → Variables
3. Crea PostgreSQL add-on
4. Deploy automático en cada push

```bash
# Railway CLI
railway link
railway up
```

#### Render

1. New → Web Service → Connect repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app`
4. Environment: Variables de `.env`
5. Add PostgreSQL Database
6. Deploy

### 3. Migraciones

```bash
# Primera vez
flask db init

# Crear migración
flask db migrate -m "Descripción del cambio"

# Aplicar migración
flask db upgrade

# En producción (automático en deploy)
```

---

## 📊 Estadísticas & Auditoría

- **Dashboard Admin** — Estadísticas en tiempo real: citas pending, confirmadas, pagos pendientes
- **Logs de Auditoría** — Ver en `/admin/auditoria`: quién hizo qué y cuándo
- **API JSON** — `/admin/api/estadisticas` para integraciones

---

## 🧪 Testing

### Instalar dependencias de test

```bash
pip install pytest pytest-cov flake8 black
```

### Ejecutar tests

```bash
pytest -v --cov=.
```

### Linting

```bash
flake8 app.py models.py routes_admin.py routes_account.py
black app.py models.py routes_admin.py routes_account.py
```

### CI/CD (GitHub Actions)

- Ejecuta tests en cada push
- Lint con flake8
- Formato con black
- Ver `.github/workflows/ci.yml`

---

## 💡 Casos de Uso

### 1. Clienta Realiza Reserva

```
1. Accede a index.html
2. Selecciona servicio + fecha/hora + datos
3. Sistema valida disponibilidad
4. POST /reservar → Booking creado
5. Email + WhatsApp enviados
6. Clienta ve en /mi-cuenta
```

### 2. Admin Confirma Cita

```
1. Login admin
2. Accede a /admin/citas
3. Ve citas "pending"
4. Hace clic "Confirmar"
5. Status → "confirmed"
6. Clienta recibe email/WhatsApp
7. Auditoría: registra quién confirmó
```

### 3. Clienta Reprograma

```
1. Accede /mi-cuenta
2. Clic en cita
3. "Reprogramar" → elige nueva fecha
4. Sistema valida disponibilidad
5. Status → "reschedule"
6. Admin recibe notificación
7. Admin confirma/rechaza en /admin/citas
```

### 4. Pago por Transferencia

```
1. Clienta ve "Anticipo: C$ 1,500"
2. Transfiere al banco
3. Sube comprobante (PNG/JPG/PDF)
4. Estado → "pending_transfer"
5. Admin revisa comprobante en /admin/citas
6. Admin marca "paid"
7. Clienta ve cita confirmada con pago
```

---

## 🌐 URLs Principales

### Públicas
- `/` — Home
- `/registro` — Crear cuenta
- `/login` — Iniciar sesión
- `/privacidad` — Política de privacidad
- `/terminos` — Términos y condiciones
- `/api/slots?date=YYYY-MM-DD` — Horarios libres (JSON)

### Autenticadas (Clienta)
- `/mi-cuenta/` — Dashboard (mis citas)
- `/mi-cuenta/cita/<id>` — Detalles de cita
- `/mi-cuenta/cita/<id>/reprogramar` — Reprogramar
- `/mi-cuenta/cita/<id>/cancelar` — Cancelar
- `/mi-cuenta/cita/<id>/comprobante` — Subir comprobante
- `/mi-cuenta/historial` — Ver historial completo
- `/mi-cuenta/perfil` — Actualizar perfil
- `/logout` — Cerrar sesión

### Admin (`/admin`)
- `/admin/` — Dashboard (estadísticas)
- `/admin/servicios` — CRUD de servicios
- `/admin/packs` — CRUD de packs/combos
- `/admin/citas` — Gestionar citas (filtrar por estado)
- `/admin/citas/<id>/confirmar` — Confirmar cita
- `/admin/citas/<id>/cancelar` — Cancelar cita
- `/admin/chats` — Ver todas las conversaciones
- `/admin/auditoria` — Logs de auditoría
- `/admin/api/estadisticas` — Datos JSON

---

## 📦 Dependencias Principales

- **Flask 2.3** — Web framework
- **SQLAlchemy** — ORM
- **Flask-Login** — Autenticación
- **Flask-SocketIO** — Chat real-time
- **Flask-Migrate** — Migraciones BD
- **Flask-Limiter** — Rate limiting
- **Flask-WTF** — CSRF protection
- **Gunicorn** — WSGI server producción
- **python-dotenv** — Variables de entorno

---

## 🛠️ Próximas Mejoras

### Corto Plazo
- [ ] Optimizar imágenes (WebP, AVIF, lazy loading)
- [ ] Tests E2E (Playwright)
- [ ] Mapa + botón WhatsApp flotante
- [ ] Sistema de packs dinámicos

### Mediano Plazo
- [ ] Pagos online (MercadoPago, Stripe)
- [ ] SMS notifications (Twilio)
- [ ] Dashboard analytics (gráficos)
- [ ] Multi-idioma (English option)

### Largo Plazo
- [ ] Mobile app (React Native)
- [ ] Sistema de reseñas
- [ ] Programa de lealtad
- [ ] Integración con Wix/Instagram

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
```bash
pip install -r requirements.txt
```

### "Database is locked" (SQLite)
SQLite no soporta concurrencia. Usar PostgreSQL en producción.

### Email no se envía
- Verifica `MAIL_ENABLED=1`
- Checa credenciales SMTP
- Revisa logs: `MAIL_ENABLED=0` loguea a stderr

### WhatsApp no llega
- Twilio: verifica SID, token y número
- Deep link: abre wa.me en navegador (debería redirigir a WhatsApp)

---

## 📄 Licencia

Privado (Beauty Nicaragua)

---

## 👨‍💼 Contacto

**Beauty Nicaragua**
- 📍 Bolonia, Managua
- 📱 +505 8877-2117
- 💬 Chat en la web
- 📧 admin@beauty-nicaragua.com

---

**Última actualización**: 2024-12-27 | v1.0 (Producción-Ready)
