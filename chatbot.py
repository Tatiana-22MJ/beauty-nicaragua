# =============================================================================
# chatbot.py — Asistente virtual "Bella" con respuestas contextuales (Nicaragua/NIO)
# =============================================================================
# Motor basado en intención por palabras clave + contexto de servicios e info del
# salón. Diseñado para respuestas fluidas, precisas y localizadas a Managua.

import random  # Variedad en saludos y respuestas genéricas (evita monotonía).
import re  # Tokenización ligera de nombres de servicios.
from difflib import SequenceMatcher  # Similitud fuzzy para entender typos del usuario.


def _similarity(a: str, b: str) -> float:
    """Calcula similitud 0–1 entre dos cadenas (útil ante errores de tipeo)."""
    return SequenceMatcher(None, a, b).ratio()  # ratio() = longitud coincidente relativa.


def _format_price(price: float) -> str:
    """Formatea un precio float como Córdobas nicaragüenses (ej. C$ 1,800)."""
    return f"C$ {price:,.0f}"  # Separador de miles estilo occidental; símbolo C$.


def _match_intent(text: str, keywords: tuple[str, ...]) -> bool:
    """True si alguna palabra clave aparece como subcadena en el mensaje."""
    return any(k in text for k in keywords)  # Búsqueda simple y rápida.


def get_bot_response(message: str, services: list, salon_info: dict) -> str:
    """
    Genera una respuesta contextual del bot Bella.

    Parámetros:
      message     — texto crudo del usuario autenticado.
      services    — lista de objetos Service activos (precios en NIO).
      salon_info  — diccionario con horarios, dirección Managua, etc.
    """
    text = message.lower().strip()  # Normaliza a minúsculas para matching.
    name = salon_info.get("bot_name", "Bella")  # Nombre comercial del asistente.
    city = salon_info.get("city", "Managua")  # Ciudad por defecto: Managua.

    # --- Saludo ---
    if _match_intent(text, ("hola", "buenas", "hey", "hi", "hello", "buenos", "saludos")):
        return random.choice([  # Alterna frases para conversación más natural.
            f"¡Hola! Soy {name}, tu asistente de Beauty en {city} 💖 ¿Buscas precios en córdobas, un tratamiento o reservar?",
            f"¡Bienvenida a Beauty Nicaragua! Soy {name}. Puedo ayudarte con Hydrafacial, depilación láser, spa y más.",
        ])

    # --- Horarios ---
    if _match_intent(text, ("horario", "hora", "abierto", "cierran", "cuando abren", "abre")):
        return (  # Devuelve los tres bloques de horario desde SalonInfo.
            f"📅 Horario en {city}:\n"
            f"• {salon_info.get('hours_weekdays', '')}\n"
            f"• {salon_info.get('hours_saturday', '')}\n"
            f"• {salon_info.get('hours_sunday', '')}"
        )

    # --- Ubicación / geolocalización ---
    if _match_intent(text, ("direccion", "dirección", "donde", "dónde", "ubicacion", "ubicación", "mapa", "llegar", "managua")):
        return (  # Dirección realista en Managua + tip de referencia.
            f"📍 Estamos en {city}, Nicaragua:\n"
            f"{salon_info.get('address', '')}\n"
            f"Referencia: cerca de zonas residenciales y plazas comerciales de fácil acceso."
        )

    # --- Contacto ---
    if _match_intent(text, ("telefono", "teléfono", "llamar", "whatsapp", "contacto", "email", "correo")):
        return (  # Teléfono +505 y email localizados.
            f"📞 Tel / WhatsApp: {salon_info.get('phone', '')}\n"
            f"✉️ Email: {salon_info.get('email', '')}"
        )

    # --- Precios en Córdobas (NIO) ---
    if _match_intent(text, ("precio", "precios", "cuesta", "coste", "costo", "tarifa", "cordoba", "córdoba", "nio", "c$")):
        lines = ["💰 Precios desde (Córdobas / NIO), adaptados al mercado de Nicaragua:"]  # Encabezado monetario.
        for s in services[:8]:  # Lista hasta 8 servicios activos.
            lines.append(f"• {s.name}: {_format_price(s.price)}")  # Cada línea con C$.
        lines.append("\nLos precios son referenciales; la valoración personalizada puede ajustar el plan.")
        lines.append("¿Querés reservar? Andá a la sección «Reservar Cita».")
        return "\n".join(lines)  # Une con saltos de línea para el chat.

    # --- Catálogo de servicios ---
    if _match_intent(text, ("servicio", "servicios", "tratamiento", "tratamientos", "ofrecen", "hacen", "menu", "menú", "catalogo", "catálogo")):
        lines = [f"✨ Tratamientos disponibles en Beauty {city}:"]  # Título del catálogo.
        for s in services:  # Itera todos los activos.
            lines.append(f"• {s.icon} {s.name} — {_format_price(s.price)}")  # Icono + nombre + precio.
        return "\n".join(lines)

    # --- Clínicas / inspiración local ---
    if _match_intent(text, ("clinica", "clínica", "la font", "medical spa", "indira", "soul wellness", "nicaragua")):
        return (  # Contextualiza la oferta inspirada en el mercado local (sin fingir afiliación).
            "En Nicaragua hay centros de referencia como Medical Spa Nicaragua, Clínica La Font, "
            "Soul Wellness & Spa y clínicas de estética en Bolonia / Plaza Las Cumbres.\n"
            "En Beauty reunimos tratamientos reales de ese mercado: Hydrafacial, depilación láser, "
            f"faciales, spa médico y cuidado capilar — con precios en córdobas ({city})."
        )

    # --- Reservas ---
    if _match_intent(text, ("reserv", "cita", "agendar", "turno", "appointment")):
        return (  # Guía paso a paso alineada con el flujo de la web.
            "📅 Para reservar en Beauty Nicaragua:\n"
            "1. Iniciá sesión (el chat y tu historial requieren cuenta)\n"
            "2. Andá a «Reservar Cita» y elegí el tratamiento\n"
            "3. Te confirmamos por email/WhatsApp en menos de 24 h"
        )

    # --- Cuenta ---
    if _match_intent(text, ("registr", "cuenta", "crear cuenta", "inscrib", "login", "sesión", "sesion")):
        return (
            "👤 Creá tu cuenta en «Registrarse».\n"
            "Solo usuarias autenticadas pueden usar este chat en tiempo real y agilizar reservas."
        )

    # --- Agradecimiento ---
    if _match_intent(text, ("gracias", "thank", "genial", "perfecto", "excelente", "bárbaro", "barbaro")):
        return random.choice([
            "¡Con gusto! Estoy acá para lo que necesités 💕",
            "¡Un placer ayudarte! ¿Querés ver precios en C$ o agendar?",
        ])

    # --- Despedida ---
    if _match_intent(text, ("adios", "adiós", "chao", "bye", "hasta", "nos vemos")):
        return f"¡Hasta pronto! Te esperamos en Beauty, {city} 🌸"

    # --- Match directo / fuzzy con un servicio concreto ---
    best_service = None  # Mejor coincidencia encontrada.
    best_score = 0.0  # Puntuación de similitud máxima.
    for s in services:  # Recorre catálogo.
        service_name = s.name.lower()  # Nombre en minúsculas.
        if service_name in text:  # Coincidencia exacta de nombre completo.
            best_service = s
            best_score = 1.0
            break  # Exacto gana; no hace falta seguir.
        tokens = [w for w in re.findall(r"\w+", service_name) if len(w) > 3]  # Tokens significativos.
        if any(tok in text for tok in tokens):  # Algún token largo aparece en el mensaje.
            best_service = s
            best_score = 0.9
            break
        score = _similarity(text, service_name)  # Fuzzy contra el nombre entero.
        if score > best_score and score >= 0.45:  # Umbral para typos leves.
            best_score = score
            best_service = s

    if best_service is not None:  # Si hubo match de servicio, responde con ficha.
        return (
            f"💫 {best_service.name} — desde {_format_price(best_service.price)} (NIO)\n"
            f"{best_service.description}\n\n"
            f"¿Reservamos? Usá el formulario «Reservar Cita» o pedime el horario."
        )

    # --- Fallback inteligente ---
    return random.choice([  # Orienta al usuario hacia intenciones conocidas.
        f"Puedo ayudarte con precios en córdobas (C$), tratamientos de {city}, horarios, ubicación o reservas. ¿Qué necesitás?",
        "No te entendí del todo. Probá preguntar por Hydrafacial, depilación láser, manicura, spa o precios.",
        f"Soy {name}. Preguntame por servicios, C$ / NIO, cómo llegar a {city} o cómo crear tu cuenta.",
    ])
