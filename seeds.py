# =============================================================================
# seeds.py — Datos iniciales Nicaragua (servicios, packs, admin, salon info)
# =============================================================================

from models import Service, ServicePackage, SalonInfo, User, db

SERVICES_SEED = [
    {
        "name": "Corte & Peinado",
        "description": (
            "Corte personalizado, brushing y peinado de evento con productos profesionales. "
            "Estilo adaptado al clima tropical de Managua."
        ),
        "price": 550.0,
        "currency": "NIO",
        "duration_minutes": 60,
        "icon": "✂️",
        "image_url": "/static/images/services/corte-peinado.png",
        "sort_order": 1,
        "quote_only": False,
    },
    {
        "name": "Coloración & Balayage",
        "description": (
            "Balayage, mechas y coloración con técnicas de baja agresión química. "
            "Acabado luminoso inspirado en salones premium de Managua."
        ),
        "price": 1800.0,
        "currency": "NIO",
        "duration_minutes": 120,
        "icon": "🎨",
        "image_url": "/static/images/services/coloracion.png",
        "sort_order": 2,
        "quote_only": False,
    },
    {
        "name": "Manicura & Pedicura",
        "description": (
            "Manicura clásica/premium y pedicura estética o clínica. "
            "Precios alineados al mercado de Managua."
        ),
        "price": 650.0,
        "currency": "NIO",
        "duration_minutes": 75,
        "icon": "💅",
        "image_url": "/static/images/services/manicura-pedicura.png",
        "sort_order": 3,
        "quote_only": False,
    },
    {
        "name": "Hydrafacial & Faciales",
        "description": (
            "Limpieza profunda, hidratación e Hydrafacial estilo medical spa: "
            "mejora textura, tono y luminosidad."
        ),
        "price": 1200.0,
        "currency": "NIO",
        "duration_minutes": 60,
        "icon": "✨",
        "image_url": "/static/images/services/tratamiento-facial.png",
        "sort_order": 4,
        "quote_only": False,
    },
    {
        "name": "Depilación Láser",
        "description": (
            "Sesión de depilación láser por zona. El precio final depende de la zona "
            "y valoración — pedí cotización personalizada."
        ),
        "price": 950.0,
        "currency": "NIO",
        "duration_minutes": 45,
        "icon": "🔦",
        "image_url": "/static/images/services/depilacion-laser.png",
        "sort_order": 5,
        "quote_only": True,  # Consultar / cotizar
    },
    {
        "name": "Maquillaje Profesional",
        "description": (
            "Maquillaje para bodas, XV años y sesiones fotográficas. "
            "Acabado de larga duración para el clima de Nicaragua."
        ),
        "price": 1100.0,
        "currency": "NIO",
        "duration_minutes": 90,
        "icon": "💄",
        "image_url": "/static/images/services/maquillaje.png",
        "sort_order": 6,
        "quote_only": False,
    },
    {
        "name": "Spa & Masajes",
        "description": (
            "Masajes terapéuticos, aromaterapia y rituales de bienestar "
            "al estilo medical spa / Soul Wellness."
        ),
        "price": 900.0,
        "currency": "NIO",
        "duration_minutes": 60,
        "icon": "🌸",
        "image_url": "/static/images/services/spa-bienestar.png",
        "sort_order": 7,
        "quote_only": False,
    },
    {
        "name": "Tratamiento Capilar",
        "description": (
            "Terapias para fortalecer el cabello, reducir caída y estimular crecimiento."
        ),
        "price": 1400.0,
        "currency": "NIO",
        "duration_minutes": 60,
        "icon": "💇",
        "image_url": "/static/images/services/tratamiento-capilar.png",
        "sort_order": 8,
        "quote_only": False,
    },
]

PACKAGES_SEED = [
    {
        "name": "Pack Spa Lujo",
        "description": "Experiencia completa de bienestar inspirada en paquetes locales (~C$2,100).",
        "includes": "Masaje 60 min · Manicura · Pedicura · Facial hidratante",
        "price": 2100.0,
        "currency": "NIO",
        "image_url": "/static/images/services/spa-bienestar.png",
        "sort_order": 1,
    },
    {
        "name": "Pack Novia Glow",
        "description": "Preparación facial + maquillaje de evento para el gran día.",
        "includes": "Hydrafacial express · Maquillaje profesional · Peinado básico",
        "price": 2800.0,
        "currency": "NIO",
        "image_url": "/static/images/services/maquillaje.png",
        "sort_order": 2,
    },
    {
        "name": "Pack Manos & Pies",
        "description": "Cuidado completo de uñas al estilo salones de Managua.",
        "includes": "Manicura premium · Pedicura clínica · Diseño simple",
        "price": 1200.0,
        "currency": "NIO",
        "image_url": "/static/images/services/manicura-pedicura.png",
        "sort_order": 3,
    },
]

SALON_INFO_SEED = {
    "about_text_1": (
        "Desde Managua, Beauty es tu espacio de belleza y bienestar inspirado en el "
        "estándar de clínicas y spas nicaragüenses: atención personalizada, tecnología "
        "estética y un ambiente cálido en el corazón de la capital."
    ),
    "about_text_2": (
        "Ofrecemos tratamientos reales del mercado local — Hydrafacial, depilación láser, "
        "faciales, spa, coloración y manicura — con precios transparentes en córdobas "
        "(C$ / NIO), packs y anticipo por transferencia."
    ),
    "years_experience": "12+",
    "happy_clients": "5K+",
    "professionals": "10",
    "address": "Residencial Bolonia, Managua, Nicaragua — cerca de Óptica Nicaragüense",
    "city": "Managua",
    "country": "Nicaragua",
    "phone": "+505 8877 2117",
    "email": "info@beauty-nicaragua.com",
    "hours_weekdays": "Lunes – Viernes: 8:00 – 18:00",
    "hours_saturday": "Sábado: 8:00 – 14:00",
    "hours_sunday": "Domingo: Cerrado",
    "bot_name": "Bella",
    "currency_code": "NIO",
    "currency_symbol": "C$",
    "map_embed": (
        "https://www.openstreetmap.org/export/embed.html"
        "?bbox=-86.290%2C12.125%2C-86.250%2C12.155&layer=mapnik&marker=12.140%2C-86.270"
    ),
    "map_link": "https://www.openstreetmap.org/?mlat=12.140&mlon=-86.270#map=15/12.140/-86.270",
}


def seed_database(app):
    """Upsert de servicios, packs, info del salón y usuario admin."""
    seed_names = {item["name"] for item in SERVICES_SEED}
    for service in Service.query.all():
        if service.name not in seed_names:
            db.session.delete(service)

    for item in SERVICES_SEED:
        service = Service.query.filter_by(name=item["name"]).first()
        if service:
            for key, value in item.items():
                setattr(service, key, value)
            service.is_active = True
        else:
            db.session.add(Service(**item))

    pack_names = {item["name"] for item in PACKAGES_SEED}
    for pack in ServicePackage.query.all():
        if pack.name not in pack_names:
            db.session.delete(pack)

    for item in PACKAGES_SEED:
        pack = ServicePackage.query.filter_by(name=item["name"]).first()
        if pack:
            for key, value in item.items():
                setattr(pack, key, value)
            pack.is_active = True
        else:
            db.session.add(ServicePackage(**item))

    for key, value in SALON_INFO_SEED.items():
        row = SalonInfo.query.filter_by(key=key).first()
        if row:
            row.value = value
        else:
            db.session.add(SalonInfo(key=key, value=value))

    admin_user = User.query.filter_by(username=app.config["ADMIN_USERNAME"]).first()
    if not admin_user:
        admin_user = User(
            username=app.config["ADMIN_USERNAME"],
            email=app.config["ADMIN_EMAIL"],
            full_name="Administradora Beauty",
            phone="+505 8877 2117",
            is_admin=True,
        )
        admin_user.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin_user)
    else:
        admin_user.is_admin = True

    db.session.commit()
