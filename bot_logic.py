"""
Lógica principal del Bot Inmobiliario AGO.
Procesa los mensajes entrantes y genera respuestas inteligentes.
Incluye: personalización por nombre, requisitos, link de estudio,
datos de inmobiliaria.
"""

from sheets_service import (
    search_properties,
    format_property_response,
    format_apply_info,
    get_available_properties
)


# Saludo inicial del bot
SALUDO_INICIAL = "¡Hola! Soy AGO, en que te puedo ayudar?"

# Almacén en memoria de sesiones de clientes
# { "521234567890": { "name": "Carlos", "state": "ready" } }
client_sessions = {}

# Palabras clave para detectar intenciones
GREETING_KEYWORDS = [
    'hola', 'buenas', 'buenos dias', 'buenas tardes', 'buenas noches',
    'hey', 'hi', 'hello', 'que tal', 'buen dia', 'saludos', 'ola'
]

LISTING_KEYWORDS = [
    'que tienen', 'qué tienen', 'que hay', 'qué hay', 'disponible',
    'disponibles', 'opciones', 'inmuebles', 'propiedades', 'catalogo',
    'catálogo', 'todo', 'todos', 'mostrar', 'ver', 'lista'
]

FAREWELL_KEYWORDS = [
    'gracias', 'chao', 'adiós', 'adios', 'hasta luego', 'bye',
    'nos vemos', 'listo', 'ok gracias', 'muchas gracias'
]

VISIT_KEYWORDS = [
    'visitar', 'visita', 'conocer', 'ver el', 'agendar', 'cita',
    'ir a ver', 'cuando puedo', 'cuándo puedo'
]

REQUIREMENTS_KEYWORDS = [
    'requisito', 'requisitos', 'necesito', 'que piden', 'qué piden',
    'documentos', 'papeles', 'condiciones', 'que necesito', 'qué necesito',
    'papeleo', 'tramite', 'trámite', 'como hago', 'cómo hago',
    'para arrendar', 'para alquilar'
]

APPLY_KEYWORDS = [
    'aplicar', 'estudio', 'formulario', 'llenar', 'diligenciar',
    'solicitar', 'solicitud', 'postular', 'como aplico', 'cómo aplico',
    'link', 'enlace', 'libertador', 'inmobiliaria', 'proceso',
    'como es el proceso', 'cómo es el proceso', 'pasos'
]


def get_session(phone_number):
    """Obtiene o crea la sesión del cliente."""
    if phone_number not in client_sessions:
        client_sessions[phone_number] = {
            "name": None,
            "state": "new"
        }
    return client_sessions[phone_number]


def detect_intent(message):
    """Detecta la intención del mensaje del cliente."""
    msg = message.lower().strip()

    # Verificar despedida
    for kw in FAREWELL_KEYWORDS:
        if kw in msg:
            return 'farewell'

    # Verificar aplicar / estudio / inmobiliaria
    for kw in APPLY_KEYWORDS:
        if kw in msg:
            return 'apply'

    # Verificar requisitos
    for kw in REQUIREMENTS_KEYWORDS:
        if kw in msg:
            return 'requirements'

    # Verificar si quiere agendar visita
    for kw in VISIT_KEYWORDS:
        if kw in msg:
            return 'visit'

    # Verificar si es solo un saludo (sin más contexto)
    words = msg.split()
    if len(words) <= 3:
        for kw in GREETING_KEYWORDS:
            if kw in msg:
                return 'greeting'

    # Verificar si pide el listado general
    for kw in LISTING_KEYWORDS:
        if kw in msg:
            return 'listing'

    # Si tiene contenido, es una búsqueda
    return 'search'


def process_message(phone_number, message):
    """
    Procesa el mensaje del cliente y genera la respuesta apropiada.
    Maneja el flujo de personalización (pedir nombre).
    """
    session = get_session(phone_number)
    intent = detect_intent(message)

    # --- FLUJO DE NOMBRE ---
    if session["state"] == "new":
        session["state"] = "awaiting_name"
        return generate_greeting_ask_name()

    if session["state"] == "awaiting_name":
        name = extract_name(message)
        session["name"] = name
        session["state"] = "ready"
        return generate_welcome_with_name(name)

    # --- FLUJO NORMAL ---
    name = session.get("name", "Amigo")

    if intent == 'greeting':
        return generate_returning_greeting(name)
    elif intent == 'farewell':
        return generate_farewell(name)
    elif intent == 'apply':
        return generate_apply_response(name, message)
    elif intent == 'requirements':
        return generate_requirements_response(name, message)
    elif intent == 'visit':
        return generate_visit_response(name, message)
    elif intent == 'listing':
        return generate_listing(name)
    elif intent == 'search':
        return generate_search_response(name, message)
    else:
        return generate_default(name)


def extract_name(message):
    """Extrae el nombre del mensaje del cliente."""
    msg = message.strip()
    remove_phrases = [
        'me llamo ', 'mi nombre es ', 'soy ', 'yo soy ',
        'hola me llamo ', 'hola soy ', 'buenas soy ',
        'hola, me llamo ', 'hola, soy ',
    ]
    msg_lower = msg.lower()
    for phrase in remove_phrases:
        if msg_lower.startswith(phrase):
            msg = msg[len(phrase):]
            break

    name = msg.strip().title()
    words = name.split()
    if len(words) > 3:
        name = ' '.join(words[:2])
    return name if name else "Amigo"


def generate_greeting_ask_name():
    """Saludo inicial + pedir nombre."""
    return f"""{SALUDO_INICIAL}

Antes de comenzar, me gustaría saber tu nombre para poder atenderte mejor. 😊

*¿Cómo te llamas?*"""


def generate_welcome_with_name(name):
    """Bienvenida personalizada."""
    return f"""¡Un gusto, *{name}*! 🤝

Ahora sí, estoy listo para ayudarte. Puedo asistirte con:

🏠 *Inmuebles disponibles* - Te muestro lo que tenemos
💰 *Precios y detalles* - Pregúntame por cualquier propiedad
📍 *Ubicaciones* - Te digo dónde queda cada inmueble
📸 *Fotos* - Te envío el catálogo de fotos
📋 *Requisitos* - Te digo qué necesitas para arrendar
📄 *Aplicar / Estudio* - Te envío el link para el estudio en línea
📅 *Agendar visita* - Coordino para que conozcas el inmueble

Solo escríbeme qué estás buscando. Por ejemplo:
_"Busco apartamento en Cali"_
_"¿Qué apartaestudios tienen disponibles?"_
_"¿Cómo aplico?"_"""


def generate_returning_greeting(name):
    """Saludo para cliente que ya se presentó."""
    return f"""¡Hola de nuevo, *{name}*! 😊

¿En qué te puedo ayudar hoy?

🏠 Escribe *"disponibles"* para ver inmuebles
📋 Escribe *"requisitos"* para conocer lo que se necesita
📄 Escribe *"aplicar"* para el estudio en línea
📅 Escribe *"visita"* para agendar una cita"""


def generate_farewell(name):
    """Despedida personalizada."""
    return f"""¡Con mucho gusto, *{name}*! 😊

Si más adelante necesitas información sobre algún inmueble, no dudes en escribirme. Estoy disponible 24/7 para ayudarte.

¡Que tengas un excelente día! 🏠
*AGO - Tu Agente Inmobiliario*"""


def generate_apply_response(name, message):
    """Respuesta con info de aplicación: estudio en línea + datos inmobiliaria."""
    results = search_properties(message)

    if results:
        prop = results[0]
        response = format_apply_info(prop)
        response += f"\n\n*{name}*, si necesitas ayuda con el proceso no dudes en escribirme. 😊"
        return response

    # Respuesta general: mostrar info de aplicación del primer inmueble disponible
    available = get_available_properties()
    if available:
        # Buscar el primer inmueble que tenga Link_Estudio o Datos_Inmobiliaria
        for prop in available:
            link_estudio = prop.get('Link_Estudio', '').strip()
            datos_inmob = prop.get('Datos_Inmobiliaria', '').strip()
            if link_estudio or datos_inmob:
                response = f"*{name}*, aquí tienes la información para aplicar:\n\n"
                if link_estudio:
                    response += f"📄 *Estudio en línea (El Libertador):*\n{link_estudio}\n\n"
                if datos_inmob:
                    response += f"🏢 *Datos de la Inmobiliaria:*\n{datos_inmob}\n\n"
                response += "Si ya tienes un inmueble en mente, dime cuál es y te doy los requisitos específicos. 😊"
                return response

    return f"""*{name}*, para aplicar a uno de nuestros inmuebles el proceso es el siguiente:

1️⃣ Escoge el inmueble que te interesa (escribe *"disponibles"* para ver opciones)
2️⃣ Te envío el link del estudio en línea de *El Libertador*
3️⃣ Llenas el formulario con tus datos
4️⃣ Coordino la visita y la firma del contrato

¿Cuál inmueble te interesa? 🏠"""


def generate_requirements_response(name, message):
    """Respuesta con requisitos del inmueble."""
    results = search_properties(message)

    if results:
        prop = results[0]
        requisitos = prop.get('Requisitos', '').strip()
        tipo = prop.get('Tipo', 'Inmueble')
        prop_id = prop.get('ID', '')

        response = f"📋 *Requisitos para {tipo}* ({prop_id})\n\n"

        if requisitos:
            response += f"*{name}*, estos son los requisitos para este inmueble:\n\n"
            response += f"{requisitos}\n"
        else:
            response += f"*{name}*, los requisitos generales son:\n\n"
            response += generate_generic_requirements()

        # Agregar link de estudio si existe
        link_estudio = prop.get('Link_Estudio', '').strip()
        if link_estudio:
            response += f"\n\n📄 *Realizar estudio en línea:* {link_estudio}"

        # Agregar datos de inmobiliaria si existen
        datos_inmob = prop.get('Datos_Inmobiliaria', '').strip()
        if datos_inmob:
            response += f"\n\n🏢 *Inmobiliaria:* {datos_inmob}"

        response += f"\n\n¿Necesitas más información o te gustaría agendar una visita, *{name}*? 😊"
        return response

    else:
        response = f"📋 *Requisitos Generales de Arrendamiento*\n\n"
        response += f"*{name}*, estos son los requisitos que normalmente se solicitan:\n\n"
        response += generate_generic_requirements()
        response += f"\n\n📌 _Algunos inmuebles pueden tener requisitos adicionales. Si me dices cuál te interesa, te doy los detalles específicos con el link para aplicar._"
        return response


def generate_generic_requirements():
    """Requisitos genéricos."""
    return """✅ Cédula de ciudadanía (copia)
✅ Certificado laboral o soporte de ingresos
✅ Referencias personales (2)
✅ Depósito de provisión de servicios (varía según el inmueble)
✅ Firma de contrato de arrendamiento"""


def generate_visit_response(name, message):
    """Respuesta para solicitud de visita."""
    results = search_properties(message)

    response = f"""📅 *¡Excelente decisión, {name}!*

Para agendar una visita, un asesor se pondrá en contacto contigo muy pronto para coordinar el día y la hora que mejor te convenga."""

    if results:
        prop = results[0]
        response += f"""

Me parece que te interesa:
🏠 *{prop.get('Tipo', '')}* en {prop.get('Ciudad', '')}
📍 {prop.get('Ubicacion', '')}

¿Es correcto?"""

    return response


def generate_listing(name):
    """Listado de inmuebles disponibles."""
    available = get_available_properties()

    if not available:
        return f"😔 Lo siento *{name}*, en este momento no tenemos inmuebles disponibles. ¡Pero pronto habrá novedades! Te avisaré cuando tengamos nuevas opciones."

    response = f"""🏠 *{name}, estos son nuestros INMUEBLES DISPONIBLES ({len(available)})*\n"""

    for i, prop in enumerate(available, 1):
        precio = prop.get('Precio', 'Consultar')
        tipo = prop.get('Tipo', 'Inmueble')
        ciudad = prop.get('Ciudad', '')
        habs = prop.get('Habitaciones', '?')
        area = prop.get('Area_m2', '?')
        prop_id = prop.get('ID', '')

        response += f"""
{'─' * 30}
*{i}. {tipo}* ({prop_id})
📍 {ciudad} | 💰 {precio}
🛏 {habs} hab. | 📐 {area} m²"""

    response += f"""

{'─' * 30}
📌 _Escríbeme el nombre o código del inmueble para ver detalles completos, fotos, requisitos y link para aplicar._"""

    return response


def generate_search_response(name, message):
    """Búsqueda de inmuebles con info completa."""
    results = search_properties(message)

    if not results:
        return f"""*{name}*, no encontré un inmueble específico con esos datos, pero tengo varias opciones que podrían interesarte. 🏠

¿Te gustaría que te muestre todos los inmuebles disponibles? Solo escribe *"disponibles"* y te muestro el catálogo completo."""

    if len(results) == 1:
        prop = results[0]
        response = f"¡Tengo justo lo que buscas, *{name}*! 🎯\n\n"
        response += format_property_response(prop, include_apply_info=True)

        # Mostrar requisitos si los tiene
        requisitos = prop.get('Requisitos', '').strip()
        if requisitos:
            response += f"\n\n📋 *Requisitos:*\n{requisitos}"

        response += "\n\n¿Te gustaría aplicar, agendar una visita o necesitas más información? 😊"
        return response

    # Múltiples resultados
    response = f"*{name}*, encontré *{len(results)} opciones* que podrían interesarte:\n"

    for prop in results:
        response += f"\n{'─' * 30}\n"
        response += format_property_response(prop)

    response += f"\n\n{'─' * 30}"
    response += f"\n📌 _¿Cuál te interesa más, {name}? Puedo darte detalles completos, requisitos y el link para aplicar._"

    return response


def generate_default(name):
    """Respuesta por defecto."""
    return f"""*{name}*, no estoy seguro de entender tu consulta. Pero puedo ayudarte con:

1️⃣ Escribe *"disponibles"* para ver todos los inmuebles
2️⃣ Escríbeme el tipo de inmueble que buscas (ej: _"apartamento en Cali"_)
3️⃣ Si ya tienes un código, envíamelo (ej: _"AGO001"_)
4️⃣ Escribe *"requisitos"* para saber qué necesitas
5️⃣ Escribe *"aplicar"* para el estudio en línea

¡Estoy aquí para ayudarte! 😊"""
