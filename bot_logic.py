from sheets_service import search_properties, format_property_response, get_available_properties

SALUDO_INICIAL = "Hola! soy *AGO*, te voy a ayudar a encontrar tu proximo hogar! ✨\n\n¿Con quién tengo el gusto de hablar? 😊"
OWNER_NUMBER = "573024929820"
client_sessions = {}

def process_message(phone_number, message):
    session = client_sessions.setdefault(phone_number, {"name": None, "state": "new"})
    msg = message.lower().strip()
    
    # Flujo de presentación
    if session["state"] == "new":
        session["state"] = "awaiting_name"
        return SALUDO_INICIAL

    if session["state"] == "awaiting_name":
        session["name"] = message.strip().title()
        session["state"] = "ready"
        return f"¡Un placer saludarte, *{session['name']}*! 🤝\n\nCuéntame, ¿qué tipo de hogar estás buscando hoy? Puedo mostrarte opciones en Cali y Jamundí. 🏠✨"

    name = session["name"]
    
    # Intenciones de ayuda humana
    if any(k in msg for k in ['asesor', 'persona', 'humano', 'visita', 'cita', 'llamar']):
        link = f"https://wa.me/{OWNER_NUMBER}?text=Hola,%20soy%20{name}%20y%20quiero%20más%20información."
        return f"¡Claro que sí, *{name}*! Entiendo perfectamente. 📱\n\nHaz clic en este enlace para hablar directamente con un asesor y coordinar todo:\n👉 {link}"

    # Búsqueda de inmuebles
    results = search_properties(msg)
    if results:
        return format_property_response(results[0], name)
    
    # Si no hay resultados claros
    return f"*{name}*, no logré encontrar algo exacto con esa descripción, pero tengo varias opciones disponibles. 🏠\n\n¿Buscas apartamento o apartaestudio? ¿En qué ciudad? ✨"
