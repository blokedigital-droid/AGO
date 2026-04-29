from sheets_service import filter_properties, format_property_list, search_properties, format_property_response, get_available_properties

SALUDO_INICIAL = "¡Hola! Soy *AGO*, te voy a ayudar a encontrar tu próximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar? 😊"
OWNER_NUMBER = "573024929820"
client_sessions = {}

def process_message(phone_number, message):
    session = client_sessions.setdefault(phone_number, {"name": None, "state": "new", "results": []})
    msg = message.lower().strip()
    
    if session["state"] == "new":
        session["state"] = "awaiting_name"
        return SALUDO_INICIAL

    if session["state"] == "awaiting_name":
        session["name"] = message.strip().title()
        session["state"] = "ready"
        return f"¡Un placer, *{session['name']}*! 🤝 ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Opciones en Cali*\n4. *Opciones en Jamundí*"

    name = session["name"]

    # Requisitos
    if any(k in msg for k in ['requisito', 'papeles', 'que piden']):
        if 'estudio' in msg or 'aparta' in msg:
            return f"*{name}*, los requisitos para *Apartaestudios* son:\n✅ Cédula\n✅ Depósito de $150.000\n✅ Contrato a 6 o 12 meses."
        return f"*{name}*, para *Apartamentos* requerimos:\n✅ Cédula\n✅ Carta Laboral\n✅ Extractos (3 meses)\n✅ Codeudor con ingresos dobles al canon."

    # Intervención humana
    if any(k in msg for k in ['asesor', 'persona', 'humano', 'visita', 'cita']):
        link = f"https://wa.me/{OWNER_NUMBER}?text=Hola,%20soy%20{name}%20y%20quiero%20más%20información."
        return f"¡Claro que sí, *{name}*! Te comunico con un asesor de inmediato:\n👉 {link}"

    # Selección por número
    if msg.isdigit() and session["results"] and int(msg) <= len(session["results"]):
        return format_property_response(session["results"][int(msg)-1], name)

    # Listados
    props = filter_properties(msg)
    if props:
        session["results"] = props
        return format_property_list(props, name)

    # Búsqueda individual
    results = search_properties(msg)
    if results:
        return format_property_response(results[0], name)

    return f"*{name}*, cuéntame qué buscas o escribe *'asesor'* para hablar con una persona. 🏠"
