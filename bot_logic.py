"""
Lógica principal del Bot Inmobiliario AGO v1.2
Maneja el flujo de venta y redirección al asesor humano.
"""

from sheets_service import (
    search_properties,
    format_property_response,
    format_apply_info,
    get_available_properties
)

SALUDO_INICIAL = "¡Hola! Soy AGO, ¿en qué te puedo ayudar?"
OWNER_NUMBER = "573024929820"  # Tu número de cierre comercial
client_sessions = {}

# --- Detección de palabras clave ---
HUMAN_KEYWORDS = ['asesor', 'persona', 'humano', 'hablar con alguien', 'llamar', 'dueño', 'inmobiliaria']
VISIT_KEYWORDS = ['visitar', 'visita', 'conocer', 'ver el', 'agendar', 'cita', 'ir a ver']

def get_session(phone_number):
    if phone_number not in client_sessions:
        client_sessions[phone_number] = {"name": None, "state": "new"}
    return client_sessions[phone_number]

def detect_intent(message):
    msg = message.lower().strip()
    if any(kw in msg for kw in HUMAN_KEYWORDS + VISIT_KEYWORDS): return 'visit'
    if any(kw in msg for kw in ['hola', 'buenas', 'hey']): return 'greeting'
    if any(kw in msg for kw in ['disponible', 'tienen', 'catalogo']): return 'listing'
    if any(kw in msg for kw in ['requisito', 'necesito', 'documento']): return 'requirements'
    if any(kw in msg for kw in ['aplicar', 'estudio', 'libertador']): return 'apply'
    return 'search'

def process_message(phone_number, message):
    session = get_session(phone_number)
    intent = detect_intent(message)
    
    if session["state"] == "new":
        session["state"] = "awaiting_name"
        return f"{SALUDO_INICIAL}\n\nAntes de comenzar, ¿cómo te llamas para darte una mejor atención? 😊"

    if session["state"] == "awaiting_name":
        session["name"] = message.strip().title()
        session["state"] = "ready"
        return f"¡Un placer, *{session['name']}*! 🤝 ¿Qué tipo de inmueble estás buscando hoy?"

    name = session.get("name", "Amigo")
    
    if intent == 'visit':
        return generate_human_redirect(name, message)
    elif intent == 'listing':
        return generate_listing(name)
    elif intent == 'requirements':
        return generate_requirements_response(name, message)
    elif intent == 'apply':
        return generate_apply_response(name, message)
    elif intent == 'search':
        return generate_search_response(name, message)
    
    return f"*{name}*, ¿te gustaría ver los inmuebles disponibles o hablar con un asesor? 😊"

def generate_human_redirect(name, message):
    """Redirige al cliente a tu número personal."""
    link = f"https://wa.me/{OWNER_NUMBER}?text=Hola,%20soy%20{name}%20y%20quiero%20más%20información."
    return f"¡Perfecto, *{name}*! 👋 Para agendar una visita o hablar con un asesor humano, haz clic en el siguiente enlace y escríbenos directamente:\n\n👉 {link}\n\n¡Un asesor te atenderá de inmediato! 🏠✨"

# --- Las demás funciones (Listing, Requirements, etc.) se mantienen igual que la versión anterior ---
def generate_listing(name):
    available = get_available_properties()
    if not available: return "No hay disponibles por ahora. 😔"
    res = f"🏠 *{name}, estos son nuestros disponibles:*\n"
    for p in available[:5]:
        res += f"\n✅ {p.get('Tipo','')} en {p.get('Ciudad','')} ({p.get('ID','')})\n💰 {p.get('Precio','')}\n"
    return res + "\nEscríbeme el código para más detalles. 🎯"

def generate_requirements_response(name, message):
    return f"*{name}*, los requisitos generales son: soporte de ingresos, cédula y un fiador. 📋\n\nSi te interesa uno en particular, dime el código y te doy los detalles exactos."

def generate_apply_response(name, message):
    return f"*{name}*, para aplicar inicia el estudio en El Libertador aquí: https://www.ellibertador.co/ 📄"

def generate_search_response(name, message):
    results = search_properties(message)
    if not results: return generate_listing(name)
    return f"¡Mira lo que encontré para ti, *{name}*! 🎯\n\n" + format_property_response(results[0])
