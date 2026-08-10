# Beauty Nicaragua — Documentación exhaustiva

**Beauty** es una aplicación web full stack de salón / spa médico localizada para **Managua, Nicaragua**, con precios en **Córdobas (C$ / NIO)**, chat en tiempo real restringido a usuarias autenticadas, animaciones buttery-smooth, narración con scroll (scrolltelling), renderizado 3D interactivo y catálogo de tratamientos alineado al mercado estético nicaragüense.

---

## Índice

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Stack tecnológico](#2-stack-tecnológico)
3. [Requisitos previos](#3-requisitos-previos)
4. [Instalación y ejecución](#4-instalación-y-ejecución)
5. [Arquitectura del sistema](#5-arquitectura-del-sistema)
6. [Estructura de carpetas](#6-estructura-de-carpetas)
7. [Moneda y geolocalización (NIO / Nicaragua)](#7-moneda-y-geolocalización-nio--nicaragua)
8. [Catálogo de servicios localizados](#8-catálogo-de-servicios-localizados)
9. [Autenticación y cuentas](#9-autenticación-y-cuentas)
10. [Chat en tiempo real (Bella)](#10-chat-en-tiempo-real-bella)
11. [Reservas](#11-reservas)
12. [UI: animaciones, scrolltelling y 3D](#12-ui-animaciones-scrolltelling-y-3d)
13. [Imágenes y assets](#13-imágenes-y-assets)
14. [Modelos de base de datos](#14-modelos-de-base-de-datos)
15. [Rutas HTTP](#15-rutas-http)
16. [Eventos WebSocket](#16-eventos-websocket)
17. [Validación cliente / servidor](#17-validación-cliente--servidor)
18. [Plantillas Jinja2 (secciones de la página)](#18-plantillas-jinja2-secciones-de-la-página)
19. [Frontend JS y CSS](#19-frontend-js-y-css)
20. [Configuración y variables de entorno](#20-configuración-y-variables-de-entorno)
21. [Flujo de datos completo](#21-flujo-de-datos-completo)
22. [Fuentes de investigación (mercado Nicaragua)](#22-fuentes-de-investigación-mercado-nicaragua)
23. [Solución de problemas](#23-solución-de-problemas)
24. [Roadmap sugerido](#24-roadmap-sugerido)

---

## 1. Resumen ejecutivo

| Aspecto | Detalle |
|--------|---------|
| Producto | Landing + reservas + chat de salón Beauty |
| Mercado | Nicaragua (Managua) |
| Moneda | Córdobas nicaragüenses (`NIO`, símbolo `C$`) |
| Backend | Flask 3 + SQLAlchemy + Flask-Login + Flask-SocketIO |
| Frontend | HTML5 semántico, CSS custom, JS vanilla, Three.js, Socket.IO |
| BD | SQLite (`instance/beauty.db`) |
| Chat | Solo usuarias **registradas / autenticadas** |
| Visual | Hero full-bleed, scrolltelling, partículas 3D, imágenes locales |

---

## 2. Stack tecnológico

### Backend
- **Flask** — framework web y enrutado.
- **Flask-SQLAlchemy** — ORM sobre SQLite.
- **Flask-Login** — sesiones de usuario y `@login_required`.
- **Flask-SocketIO** — WebSockets para el chat en tiempo real.
- **Werkzeug** — hash de contraseñas (`generate_password_hash` / `check_password_hash`).

### Frontend
- **Jinja2** — plantillas server-side.
- **CSS custom** — variables de diseño, animaciones cubic-bezier buttery.
- **IntersectionObserver** — reveals y scrolltelling.
- **Three.js (r128)** — escena 3D de partículas en el hero.
- **Socket.IO client** — canal bidireccional del chat.

---

## 3. Requisitos previos

- **Python 3.10+** (anotaciones `str | None` y sintaxis moderna).
- pip / entorno virtual recomendado.
- Navegador moderno con WebGL (para el 3D) y WebSockets.

---

## 4. Instalación y ejecución

```bash
# 1) Ir a la carpeta del proyecto
cd c:\Users\Tatiana\Documents\beauty

# 2) (Opcional) Crear y activar entorno virtual
py -m venv .venv
.\.venv\Scripts\activate

# 3) Instalar dependencias
py -m pip install -r requirements.txt

# 4) Arrancar el servidor (Flask + SocketIO)
py app.py
```

Abrí en el navegador: [http://127.0.0.1:5000](http://127.0.0.1:5000)

> **Importante:** no abras los HTML estáticos a mano. El chat y las rutas requieren el servidor Flask con SocketIO (`py app.py`).

---

## 5. Arquitectura del sistema

```
┌─────────────────┐     HTTP / Jinja      ┌──────────────────┐
│  Navegador      │ ◄──────────────────► │  Flask (app.py)  │
│  HTML/CSS/JS    │                      │  Rutas + Login   │
│  Three.js       │     WebSocket        │                  │
│  Socket.IO      │ ◄──────────────────► │  Flask-SocketIO  │
└─────────────────┘                      └────────┬─────────┘
                                                  │
                                         ┌────────▼─────────┐
                                         │  SQLite (ORM)    │
                                         │  users, services │
                                         │  bookings, chat  │
                                         │  salon_info      │
                                         └──────────────────┘
```

1. El cliente pide `/` → Flask consulta `Service` + `SalonInfo` → renderiza `index.html`.
2. Registro/login → Flask-Login guarda la sesión en cookie firmada.
3. Chat: el cliente emite `send_message` → el servidor valida auth → `chatbot.get_bot_response` → emite `bot_message`.
4. Reserva: POST `/reservar` → validadores → inserta `Booking`.

---

## 6. Estructura de carpetas

```
beauty/
├── app.py                 # Factory Flask, seeds NIO, rutas, SocketIO
├── chatbot.py             # Motor contextual de Bella (precios C$, Managua)
├── config.py              # SECRET_KEY, BD, moneda NIO, locale es_NI
├── models.py              # User, Service, Booking, ChatMessage, SalonInfo
├── validators.py          # Validación server-side
├── requirements.txt       # Dependencias pinneadas
├── README.md              # Esta documentación
├── instance/
│   └── beauty.db          # SQLite (se crea al arrancar)
├── templates/
│   ├── base.html          # Layout: fonts, CSS, Three.js, Socket.IO
│   ├── index.html         # Landing completa (hero→footer→chat)
│   └── auth/
│       ├── login.html
│       └── register.html
└── static/
    ├── css/style.css      # Tema + animaciones + scrolltelling + chat
    ├── js/
    │   ├── main.js        # Nav, reveals, scrolltelling, booking validation
    │   ├── chat.js        # Socket.IO + gate de autenticación
    │   ├── scene3d.js     # Partículas 3D interactivas (Three.js)
    │   └── validation.js  # Validación de formularios auth
    └── images/
        ├── hero-beauty.png
        ├── salon-interior.png
        └── services/      # 8 imágenes de tratamientos generadas
            ├── corte-peinado.png
            ├── coloracion.png
            ├── manicura-pedicura.png
            ├── tratamiento-facial.png
            ├── depilacion-laser.png
            ├── maquillaje.png
            ├── spa-bienestar.png
            └── tratamiento-capilar.png
```

---

## 7. Moneda y geolocalización (NIO / Nicaragua)

### Configuración (`config.py`)
- `CURRENCY_CODE = "NIO"`
- `CURRENCY_SYMBOL = "C$"`
- `COUNTRY_CODE = "NI"`
- `COUNTRY_NAME = "Nicaragua"`
- `DEFAULT_LOCALE = "es_NI"`
- `TIMEZONE = "America/Managua"`

### Presentación en UI
- Filtro Jinja `{{ price|nio }}` → `C$ 1,800`.
- Context processor inyecta `currency_symbol`, `currency_code`, `country_name` en todas las plantillas.
- Columna `Service.currency` guarda `"NIO"` por servicio.
- Teléfonos con prefijo **+505**; placeholders y validación adaptados.
- Dirección y horarios del salón en **Residencial Bolonia, Managua**.
- Schema.org `BeautySalon` con `addressCountry: "NI"` y `currenciesAccepted: "NIO"`.

### Semilla forzada
Al arrancar, `seed_database()` **actualiza** precios, textos e imágenes y **elimina** servicios obsoletos (p. ej. semillas antiguas en euros / Madrid).

---

## 8. Catálogo de servicios localizados

Tratamientos inspirados en la oferta real de clínicas y spas de Nicaragua (Medical Spa Nicaragua, clínicas estéticas en Bolonia, Soul Wellness & Spa, La Font, salones de manicura/pedicura de Managua). Precios **referenciales** en córdobas:

| Servicio | Precio desde (NIO) | Notas de mercado |
|----------|--------------------|------------------|
| Corte & Peinado | C$ 550 | Salones Managua ~C$450–800 |
| Coloración & Balayage | C$ 1,800 | Coloración premium |
| Manicura & Pedicura | C$ 650 | Manicura ~C$455; pedicura ~C$600+ |
| Hydrafacial & Faciales | C$ 1,200 | Medical spa / Hydrafacial |
| Depilación Láser | C$ 950 | Sesión por zona (clínicas estéticas) |
| Maquillaje Profesional | C$ 1,100 | Eventos / bodas / XV |
| Spa & Masajes | C$ 900 | Spa individual; paquetes ~C$2,100 |
| Tratamiento Capilar | C$ 1,400 | Fortalecimiento / caída |

> Los precios son orientativos para la plataforma demo. En producción se recomienda cotización tras valoración.

---

## 9. Autenticación y cuentas

### Registro (`/registro`)
Campos: nombre, usuario, email, teléfono (+505), contraseña, confirmación.  
Validación doble (JS + Python). Contraseña hasheada. Autologin tras crear cuenta.

### Login (`/login`)
Identificador = **email o username** + contraseña. Opción “Recordarme”.

### Logout (`/logout`)
Requiere `@login_required`. Limpia la sesión Flask-Login.

### Por qué el chat exige cuenta
1. Evita abuso anónimo del WebSocket.
2. Asocia `ChatMessage.user_id` al historial.
3. Experiencia personalizada (“¡Hola, María!”).

---

## 10. Chat en tiempo real (Bella)

### Reglas de acceso
- **Backend:** `connect` retorna `False` si `not current_user.is_authenticated` y emite `auth_required`.
- **Backend:** `send_message` vuelve a comprobar auth.
- **Frontend:** si `data-authenticated="false"`, no abre socket; muestra botones de login/registro.

### Inteligencia del bot (`chatbot.py`)
Intenciones detectadas por keywords + fuzzy matching (`difflib`):
- Saludos, horarios, dirección Managua, contacto +505.
- Precios en **C$ / NIO**.
- Catálogo de servicios.
- Contexto de clínicas del mercado nicaragüense.
- Reservas, registro, agradecimientos, despedidas.
- Ficha detallada si el mensaje menciona un servicio (o un typo cercano).

Las respuestas se persisten en `chat_messages` (sender `user` / `bot`).

---

## 11. Reservas

Formulario en `#reservar` → POST `/reservar`:
1. Valida nombre, email, teléfono, servicio existente, fecha.
2. Crea `Booking` (vincula `user_id` si hay sesión).
3. Flash de éxito y redirect al ancla `#reservar`.

Fecha mínima = hoy (seteada en `main.js`).

---

## 12. UI: animaciones, scrolltelling y 3D

### Buttery smooth
- Transiciones globales `cubic-bezier(0.22, 1, 0.36, 1)`.
- Reveals con `IntersectionObserver` (una sola vez).
- Hover con `transform` (composited, sin layout thrash).
- Respeto a `prefers-reduced-motion`.

### Scrolltelling (`#experiencia`)
1. Escenario **sticky** con imagen + caption.
2. Tres capítulos (`scrolltell-chapter`) de ~70vh.
3. Al entrar un capítulo al viewport (~55%), JS crossfadea imagen y texto (bienvenida → tratamiento → renovación).

### 3D interactivo (`scene3d.js`)
- Esfera de ~900 partículas + torus.
- Colores de marca (rosa / azul).
- Responde a `pointermove` / `touchmove`.
- Loop `requestAnimationFrame` a ~60 fps.
- Canvas con `mix-blend-mode: screen` sobre la foto hero.

---

## 13. Imágenes y assets

Todas las imágenes de servicios y hero son **archivos locales** en `static/images/` (no dependen de Unsplash).  
Si una URL fallara, `onerror` en las plantillas cae a `salon-interior.png` o `hero-beauty.png`.

---

## 14. Modelos de base de datos

| Modelo | Tabla | Rol |
|--------|-------|-----|
| `User` | `users` | Cuentas (hash password, phone +505) |
| `Service` | `services` | Catálogo NIO + `image_url` + `currency` |
| `Booking` | `bookings` | Solicitudes de cita |
| `ChatMessage` | `chat_messages` | Historial del chat |
| `SalonInfo` | `salon_info` | Key/value (dirección, horarios, textos) |

Migraciones ligeras en `migrate_schema()` añaden `image_url`, `currency`, `user_id` si faltan.

---

## 15. Rutas HTTP

| Método | Ruta | Vista | Descripción |
|--------|------|-------|-------------|
| GET | `/` | `index` | Landing completa |
| GET/POST | `/registro` | `register` | Alta de usuaria |
| GET/POST | `/login` | `login` | Inicio de sesión |
| GET | `/logout` | `logout` | Cierre de sesión |
| POST | `/reservar` | `reservar` | Alta de booking |

---

## 16. Eventos WebSocket

| Evento | Dirección | Descripción |
|--------|-----------|-------------|
| `connect` | cliente→server | Exige auth; `join_room(session_id)` |
| `connected` | server→cliente | Confirma sala + nombre |
| `auth_required` | server→cliente | Sin sesión o sesión expirada |
| `send_message` | cliente→server | `{ message: "..." }` |
| `bot_message` | server→cliente | Respuesta de Bella |
| `user_message` | server→cliente | Eco opcional |

---

## 17. Validación cliente / servidor

| Campo | Cliente (`validation.js`) | Servidor (`validators.py`) |
|-------|---------------------------|----------------------------|
| Nombre | min 2 | min 2 / max 120 |
| Email | regex | regex |
| Teléfono | 8–20 dígitos/símbolos | idem (+ tip +505) |
| Usuario | `[A-Za-z0-9_]{3,30}` | idem |
| Contraseña | ≥8, letras+números | idem + confirm |
| Fecha | no pasada | no vacía |
| Servicio | required | existe en BD |

---

## 18. Plantillas Jinja2 (secciones de la página)

### `base.html`
Layout HTML5 `lang="es-NI"`, meta SEO/OG, fonts, CSS, Socket.IO, Three.js, `main.js`, `scene3d.js`.

### `index.html` — secciones
1. **Header / Nav** — marca + enlaces + auth.
2. **Hero `#inicio`** — marca Beauty., claim Nicaragua/NIO, CTAs, foto + canvas 3D, scroll cue.
3. **Scrolltelling `#experiencia`** — 3 actos narrativos.
4. **Beneficios** — localización, expertos, premium, chat auth.
5. **Servicios `#servicios`** — grilla con precios `|nio` e imágenes locales.
6. **Galería `#galeria`** — mosaico de trabajos.
7. **Nosotros `#nosotros`** — historia Managua + stats.
8. **Testimonios** — voces localizadas (Bolonia, Las Colinas, Plaza Las Cumbres).
9. **Reservar `#reservar`** — formulario.
10. **CTA cuenta** — solo si no hay sesión.
11. **Footer `#contacto`** — dirección, +505, horarios.
12. **Chat widget** — Bella (gate auth).

### Auth
`login.html` / `register.html` — formularios centrados con el mismo sistema visual.

---

## 19. Frontend JS y CSS

| Archivo | Función |
|---------|---------|
| `main.js` | Nav scrolled, menú móvil, reveals, scrolltelling, date min, booking validation |
| `chat.js` | Gate auth, Socket.IO, typing indicator, escape XSS |
| `scene3d.js` | Three.js partículas + torus interactivo |
| `validation.js` | API `BeautyValidation` + auto-attach auth forms |
| `style.css` | Tokens, hero, scrolltell, servicios, chat, responsive, reduced-motion |

---

## 20. Configuración y variables de entorno

| Variable | Default | Uso |
|----------|---------|-----|
| `SECRET_KEY` | `beauty-dev-key-…` | Firmar cookies (cambiar en prod) |
| `DATABASE_URL` | `sqlite:///…/instance/beauty.db` | URI SQLAlchemy |

Ejemplo PowerShell:

```powershell
$env:SECRET_KEY="tu-clave-segura"
py app.py
```

---

## 21. Flujo de datos completo

### Primera visita
1. `create_app()` → `db.create_all()` → `migrate_schema()` → `seed_database()`.
2. GET `/` → servicios NIO + info Managua → HTML.

### Registro → Chat
1. POST `/registro` → User + login.
2. Abre Bella → `io()` → `connect` OK → `connected`.
3. Escribe “precios” → `send_message` → Bella lista precios en C$ → `bot_message`.

### Reserva
1. Completa formulario → validación JS.
2. POST `/reservar` → validación Python → `Booking` → flash.

---

## 22. Fuentes de investigación (mercado Nicaragua)

La oferta y los rangos de precio se contrastaron con información pública de:
- Medical Spa Nicaragua (Hydrafacial, depilación láser, faciales, masajes).
- Clínica estética Dra. Indira Herrera (Bolonia, Managua — faciales, corporales, capilares, láser, spa médico).
- Soul Wellness & Spa (Plaza Las Cumbres — masajes, bienestar).
- Clínica La Font (láser / estética médico-quirúrgica).
- Salones de manicura/pedicura Managua (rangos ~C$455–1,200; pedicuras clínicas ~C$600–1,000).
- Referencias de spa/paquetes en el país (~C$2,100 paquetes combinados).

Beauty **no afirma afiliación** con esas marcas; las usa como referencia de mercado para localizar el catálogo demo.

---

## 23. Solución de problemas

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| Chat no responde | No hay sesión | Registrate / iniciá sesión |
| `auth_required` | Cookie expirada | Volvé a loguearte |
| Precios en € | BD vieja sin re-seed | Borrá `instance/beauty.db` y reiniciá `py app.py` |
| Imágenes rotas | Ruta incorrecta | Verificá `static/images/services/*.png` |
| Sin 3D | WebGL / Three no cargó | Revisá consola; usá Chrome/Edge actualizado |
| Puerto ocupado | Otro proceso en 5000 | Cambiá el puerto en `socketio.run(...)` |

---

## 24. Roadmap sugerido

- Panel admin para editar precios NIO sin tocar código.
- Confirmación de citas por WhatsApp Business (+505).
- Pagos en córdobas (pasarela local).
- Alembic para migraciones formales.
- Tests automatizados (pytest + Playwright).
- Deploy con Gunicorn + eventlet / gevent detrás de Nginx.

---

## Licencia y créditos

Proyecto educativo / demo de salón **Beauty Nicaragua**.  
Tipografías: Cormorant Garamond + Outfit (Google Fonts).  
3D: Three.js. Chat: Socket.IO.

---

**Beauty.** — Managua, Nicaragua · Precios en C$ (NIO)
