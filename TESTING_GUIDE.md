# 🧪 GUÍA DE TESTING — Beauty Nicaragua v1.0

**Status**: ✅ App corriendo en http://127.0.0.1:5000

---

## 1️⃣ FLUJO DE CLIENTA (Registrarse → Reservar → Ver Cita)

### Paso 1: Registrarse
1. Abre http://127.0.0.1:5000/registro
2. Completa:
   ```
   Nombre completo:  Tatiana Flores
   Usuario:          tatiana_flores
   Email:            tatiana@example.com
   Teléfono:         50588772117 (o tu número)
   Contraseña:       Test123!
   Confirmar:        Test123!
   ```
3. Botón: **CREAR CUENTA**
   - ✅ Te debe loguear automáticamente
   - ✅ Deberías estar en `/` con "¡Bienvenida!" flash

### Paso 2: Hacer Reserva
1. En el home, desplázate a **"Reservar Ahora"**
2. Formulario de reserva:
   ```
   Nombre:           Tatiana Flores
   Email:            tatiana@example.com
   Teléfono:         50588772117
   Servicio:         [Elige uno, ej: Facial]
   Fecha preferida:  [Mañana o próximos días]
   Hora preferida:   [Elige una disponible]
   Mensaje:          Quisiera confirmar disponibilidad
   ```
3. Botón: **RESERVAR**
   - ✅ Flash: "Gracias Tatiana! Cita solicitada..."
   - ✅ Te redirige a `/mi-cuenta`

### Paso 3: Ver "Mis Citas"
1. Ya estás en http://127.0.0.1:5000/mi-cuenta
2. Deberías ver:
   ```
   [PENDING] Facial — 2024-12-28 10:00
   Estado: Pendiente de Confirmación
   Precio: C$ 1,500
   ```
3. Botones disponibles:
   - 📋 **Detalles** → Ver info completa
   - 🔄 **Reprogramar** → Cambiar fecha/hora
   - ❌ **Cancelar** → Cancelar cita

### Paso 4: Reprogramar (Opcional)
1. Haz clic en **REPROGRAMAR**
2. Selecciona nueva fecha/hora (deben estar libres)
3. Botón: **SOLICITAR REPROGRAMACIÓN**
   - ✅ Status: pending → reschedule
   - ✅ Admin recibe notificación

---

## 2️⃣ FLUJO DE ADMIN (Confirmar Cita, Gestionar Servicios)

### Paso 1: Login como Admin
1. Abre http://127.0.0.1:5000/logout (para desloguear clienta actual)
2. Abre http://127.0.0.1:5000/login
3. Credenciales:
   ```
   Usuario/Email:    admin
   Contraseña:       Admin123!
   ```
4. Botón: **INICIAR SESIÓN**
   - ✅ Te debe redirigir a `/admin/`

### Paso 2: Dashboard Admin
1. En http://127.0.0.1:5000/admin/ deberías ver:
   ```
   📊 ESTADÍSTICAS
   • Citas Pendientes: 1 (la de Tatiana)
   • Citas Confirmadas: 0
   • Citas Hoy: [N]
   • Pagos Pendientes: 0
   • Usuarios: 2 (admin + Tatiana)
   • Mensajes de Chat: [N]
   
   📋 CITAS RECIENTES
   [Facial] Tatiana Flores | 2024-12-28 10:00 | [PENDING]
   ```

### Paso 3: Ver Todas las Citas
1. Haz clic en **"Citas"** o ve a http://127.0.0.1:5000/admin/citas
2. Deberías ver:
   ```
   [Filtros]
   Estado: [Todos] [Pending] [Confirmed] [Cancelled] [Completed]
   
   [TABLA DE CITAS]
   ID | Clienta | Servicio | Fecha | Hora | Estado | Pago | Acciones
   1  | Tatiana | Facial   | 2024-12-28 | 10:00 | pending | unpaid | [✏️ Editar]
   ```

### Paso 4: Confirmar Cita
1. Haz clic en el botón **[Editar]** de la cita de Tatiana
2. Formulario:
   ```
   Estado:          [pending ▼] → Elige "confirmed"
   Estado de Pago:  [unpaid ▼] → Déjalo igual
   Notas:           "Confirmado. Te llamaremos mañana"
   ```
3. Botón: **ACTUALIZAR**
   - ✅ Status: pending → confirmed
   - ✅ Tatiana recibe email: "Tu cita está CONFIRMADA ✅"
   - ✅ Se registra en auditoría

### Paso 5: Gestionar Servicios
1. Ve a http://127.0.0.1:5000/admin/servicios
2. Deberías ver lista de servicios (Facial, Masaje, etc.)
3. Opciones:
   - **Ver/Editar**: Cambiar nombre, precio, descripción
   - **Crear Nuevo**: Botón "+ Nuevo Servicio"
   - **Eliminar**: ❌ botón

#### Crear un Servicio Nuevo
1. Botón: **+ NUEVO SERVICIO**
2. Formulario:
   ```
   Nombre:           Spa Relax Package
   Descripción:      Masaje + facial + manos. 2 horas.
   Precio (C$):      2100
   Duración (min):   120
   Icono:            🧖
   Imagen URL:       (dejar vacío por ahora)
   "Consultar Precio": [sin marcar]
   Ordenar:          10
   ```
3. Botón: **CREAR SERVICIO**
   - ✅ Aparece en la lista
   - ✅ Disponible para reservas

### Paso 6: Gestionar Packs
1. Ve a http://127.0.0.1:5000/admin/packs
2. Similar a servicios:
   ```
   • Ver/Editar
   • Crear: nombre, descripción, incluye (qué lleva), precio
   • Eliminar
   ```

---

## 3️⃣ FLUJO DE NOTIFICACIONES (Email + WhatsApp)

### Email (Dev Mode)
En desarrollo, los emails NO se envían reales, se **loguean en consola**.

**Cuando Tatiana hace reserva**, en la consola deberías ver:
```
[EMAIL-MOCK] to=tatiana@example.com subject=✨ Solicitud recibida — Facial

Hola Tatiana,

✨ Recibimos tu solicitud de cita para «Facial» el 2024-12-28 10:00.

📋 Estado: PENDING
💳 Pago: UNPAID
💰 Anticipo sugerido: C$ 450

Te confirmaremos pronto. También podés escribirnos por WhatsApp.
📱 https://wa.me/50588772117?text=...

— Beauty Nicaragua (Managua)
📍 Bolonia, Managua
```

**Cuando Admin confirma**, otro email:
```
[EMAIL-MOCK] to=tatiana@example.com subject=✅ Actualización de cita — confirmed

Hola Tatiana,

✅ Tu cita «Facial» (2024-12-28 10:00) ahora está: CONFIRMED.
...
```

### WhatsApp (Dev Mode)
Similarly, WhatsApp logs to console:
```
[WHATSAPP-MOCK] to=+50588772117 msg=Hola Tatiana,

✨ Recibimos tu solicitud para Facial el 2024-12-28 10:00.
...
```

Para **testing REAL en producción**, necesitas:
```
MAIL_ENABLED=1
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

---

## 4️⃣ FLUJO DE CHAT (Real-time)

### Chat Clienta
1. Loguéate como clienta (Tatiana)
2. Busca el **botón CHAT** (esquina inferior derecha o en /mi-cuenta)
3. Pregunta algo:
   ```
   "¿Qué servicios tienen disponibles?"
   ```
4. El bot responde automáticamente:
   ```
   "Hola Tatiana! Tenemos Facial, Masaje, Manicura, y más.
   ¿Quieres conocer precios o disponibilidad?"
   ```
5. Intercambia mensajes (máx 500 caracteres)

### Ver Chat en Admin
1. Loguéate como admin
2. Ve a http://127.0.0.1:5000/admin/chats
3. Deberías ver:
   ```
   [Conversación: session_id_xxx]
   Usuario: Tatiana Flores
   
   [user]: ¿Qué servicios tienen disponibles?
   [bot]:  Hola Tatiana! Tenemos...
   
   [user]: ¿Cuál es el precio del masaje?
   [bot]:  El masaje está a C$ 800...
   ```

---

## 5️⃣ FLUJO DE PAGOS (Anticipo)

### Clienta Sube Comprobante
1. En `/mi-cuenta`, busca tu cita
2. Botón: **SUBIR COMPROBANTE**
3. Carga un archivo:
   - Tipos: PNG, JPG, WEBP, PDF
   - Tamaño máx: 4 MB
   - Ejemplo: screenshot de transferencia

4. El comprobante se guarda en `instance/uploads/`
   - Nombre: `proof_[booking_id]_[uuid].jpg`

### Admin Verifica Pago
1. En `/admin/citas`, busca la cita
2. Haz clic **EDITAR**
3. Campo: **Estado de Pago**
   ```
   [unpaid ▼]
   • unpaid (no pagado)
   • pending_transfer (comprobante pendiente revisión)
   • paid (pagado y confirmado)
   ```
4. Cambia a: **paid**
5. Botón: **ACTUALIZAR**
   - ✅ Clienta recibe notificación: "Tu anticipo fue confirmado ✅"

---

## 6️⃣ FLUJO DE AUDITORÍA

### Ver Logs de Admin
1. Ve a http://127.0.0.1:5000/admin/auditoria
2. Deberías ver registro de todas las acciones:
   ```
   | Usuario | Acción | Detalle | Fecha |
   |---------|--------|---------|-------|
   | admin   | booking_confirm | #1 | 2024-12-27 13:28 |
   | admin   | service_create | Spa Relax | 2024-12-27 13:25 |
   | tatiana | booking_reschedule | #1: 2024-12-28→2024-12-29 | 2024-12-27 13:20 |
   ```

---

## 7️⃣ PRUEBAS ADICIONALES

### API: Horarios Disponibles
```bash
curl "http://127.0.0.1:5000/api/slots?date=2024-12-28"
```

Respuesta JSON:
```json
{
  "ok": true,
  "slots": ["09:00", "10:00", "11:00", "14:00", "15:00"],
  "closed": false
}
```

### Horario No Disponible
```bash
curl "http://127.0.0.1:5000/api/slots?date=2024-12-27"
```

(Hoy probablemente cierre temprano o esté cerrado domingo)

```json
{
  "ok": true,
  "slots": [],
  "closed": true
}
```

### Error: Fecha Inválida
```bash
curl "http://127.0.0.1:5000/api/slots?date=fecha-mala"
```

```json
{
  "ok": false,
  "slots": [],
  "error": "Fecha inválida"
}
```

---

## 8️⃣ PRUEBAS DE SEGURIDAD

### Rate Limiting
1. Intenta login 11 veces en 1 minuto:
   ```bash
   for i in {1..11}; do
     curl -X POST http://127.0.0.1:5000/login \
       -d "identifier=admin&password=Admin123!" \
       -c cookies.txt
   done
   ```
2. En la 11ª, deberías recibir:
   ```
   429 Too Many Requests
   "Rate limit exceeded"
   ```

### CSRF Protection
1. Intenta POST sin token CSRF:
   ```bash
   curl -X POST http://127.0.0.1:5000/reservar \
     -d "full_name=Test&email=test@test.com"
   ```
2. Deberías recibir error de CSRF

---

## 9️⃣ CHECKLIST DE TESTING

- [ ] **Registrarse** — Crear cuenta cliente
- [ ] **Reservar** — Hacer cita (ver en /mi-cuenta)
- [ ] **Disponibilidad** — API retorna horarios
- [ ] **Admin Login** — Acceder a /admin
- [ ] **Confirmar Cita** — Cambiar status pending → confirmed
- [ ] **Crear Servicio** — Nuevo en admin panel
- [ ] **Reprogramar** — Cambiar fecha/hora
- [ ] **Chat** — Enviar mensaje, ver en admin
- [ ] **Pago** — Subir comprobante
- [ ] **Auditoría** — Ver logs de acciones
- [ ] **Email Mock** — Ver en consola
- [ ] **WhatsApp Mock** — Ver en consola
- [ ] **Error Pages** — Probar /404, /500
- [ ] **Rate Limit** — Intentar login 11+ veces
- [ ] **CSRF** — POST sin token

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
```bash
.\.venv\Scripts\activate.ps1
pip install -r requirements.txt
```

### "Port 5000 already in use"
```bash
# Matar proceso existente
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# O cambia puerto
set FLASK_ENV=development
python app.py --port 5001
```

### "Database is locked"
SQLite tiene limitaciones. Si aparece, reinicia la app o usa PostgreSQL.

### Emails no aparecen en consola
Verifica:
- `MAIL_ENABLED=0` (debe estar en 0 para dev)
- Consola debe estar corriendo (`python app.py`)

---

## 📞 URLs Rápidas

| URL | Descripción |
|-----|-------------|
| http://127.0.0.1:5000/ | Home |
| http://127.0.0.1:5000/registro | Registrarse |
| http://127.0.0.1:5000/login | Login |
| http://127.0.0.1:5000/mi-cuenta | Mis citas |
| http://127.0.0.1:5000/admin | Admin panel |
| http://127.0.0.1:5000/admin/servicios | Servicios |
| http://127.0.0.1:5000/admin/citas | Citas |
| http://127.0.0.1:5000/admin/chats | Chats |
| http://127.0.0.1:5000/admin/auditoria | Auditoría |
| http://127.0.0.1:5000/privacidad | Privacy |
| http://127.0.0.1:5000/terminos | Terms |

---

## 🎬 Video Script (Si quieres grabar demo)

```
0:00-0:30   Intro: "Beauty Nicaragua v1.0 Production-Ready"
0:30-1:30   Registrarse como clienta
1:30-2:30   Hacer reserva
2:30-3:00   Ver "Mis citas"
3:00-3:30   Logout, login como admin
3:30-4:00   Dashboard admin con estadísticas
4:00-4:30   Confirmar cita (status: pending → confirmed)
4:30-5:00   Ver email mock en consola
5:00-5:30   Crear servicio nuevo
5:30-6:00   Ver chat e interactuar
6:00-6:30   Conclusión: "Listo para Railway/Render"
```

---

**¡A probar! 🧪**

Cualquier error, vélo en la consola y comparte aquí. ✅
