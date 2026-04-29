from sheets_service import search_properties, format_property_response, get_available_properties

SALUDO_INICIAL = "¡Hola! Soy *AGO*, tu asistente personal del Grupo Inmobiliario. 🏠✨\n\nTe voy a ayudar a encontrar tu próximo hogar. Para empezar, ¿con quién tengo el gusto de hablar? 😊"
OWNER_NUMBER = "573024929820"
client_sessions = {}

def process_message(phone_number, message):
    session = client_sessions.setdefault(phone_number, {"name": None, "state": "new", "last_id": None})
    msg = message.lower().strip()
    
    if session["state"] == "new":
        session["state"] = "awaiting_name"
        return SALUDO_INICIAL

    if session["state"] == "awaiting_name":
        session["name"] = message.strip().title()
        session["state"] = "ready"
        return f"¡Un placer saludarte, *{session['name']}*! 🤝\n\nEstoy listo. ¿Qué estás buscando hoy?\n\n📍 _Cali o Jamundí?_\n🏠 _Apartamento o Apartaestudio?_\n💰 _Algún presupuesto en mente?_"

    name = session["name"]
    
    # Intención: Hablar con humano o cita
    if any(k in msg for k in ['asesor', 'persona', 'humano', 'visita', 'cita', 'llamar']):
        link = f"https://wa.me/{OWNER_NUMBER}?text=Hola,%20soy%20{name}%20y%20quiero%20más%20información."
        return f"¡Entendido, *{name}*! 📱 Te voy a comunicar directamente con mi jefe para cerrar los detalles.\n\nHaz clic aquí:\n👉 {link}"

    # Intención: Requisitos específicos
    if any(k in msg for k in ['requisito', 'papeles', 'necesito', 'documento']):
        # Si el cliente ya estaba viendo un inmueble, le damos sus requisitos
        return f"*{name}*, para nuestras propiedades pedimos:\n\n✅ Cédula\n✅ Soporte de ingresos\n✅ Fiador\n\n¿Te gustaría que te envíe el link del estudio de El Libertador? 📄"

    # Búsqueda
    results = search_properties(msg)
    if results:
        session["last_id"] = results[0].get('ID')
        return format_property_response(results[0], name)
    
    # Fallback amable
    return f"No te preocupes *{name}*, sigamos buscando. 🔍 ¿Te gustaría ver todos los inmuebles disponibles? Escribe *'lista'*."
