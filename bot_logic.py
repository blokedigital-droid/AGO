from sheets_service import filter_properties, format_property_list, search_properties, format_property_response, get_available_properties

SALUDO_INICIAL = "¡Hola! Soy *AGO*, te voy a ayudar a encontrar tu próximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar? 😊"
OWNER_NUMBER = "573024929820"
client_sessions = {}

def process_message(phone_number, message):
    session = client_sessions.setdefault(phone_number, {"name": None, "state": "new", "results": [], "pending_query": None})
    msg = message.lower().strip()
    
    # 1. Identificar si el primer mensaje ya trae una búsqueda
    if session["state"] == "new":
        # Si el mensaje no es un simple saludo, guardamos la búsqueda
        if len(msg.split()) > 1 or any(k in msg for k in ['apto', 'cali', 'jamundi', 'donde', 'precio']):
            session["pending_query"] = msg
        session["state"] = "awaiting_name"
        return SALUDO_INICIAL

    # 2. Capturar el nombre y procesar búsqueda pendiente
    if session["state"] == "awaiting_name":
        session["name"] = message.strip().title()
        session["state"] = "ready"
        welcome = f"¡Un placer, *{session['name']}*! 🤝"
        
        if session["pending_query"]:
            query = session["pending_query"]
            session["pending_query"] = None
            results = search_properties(query)
            if results:
                return f"{welcome} Sobre lo que preguntabas:\n\n" + format_property_response(results[0], session["name"])
        
        return f"{welcome} ¿Qué tipo de hogar buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Opciones en Cali*\n4. *Opciones en Jamundí*"

    name = session["name"]

    # 3. Lógica de "Ya agendé"
    if any(k in msg for k in ['ya agende', 'ya agendé', 'listo la cita', 'ya tengo cita']):
        return f"¡Excelente noticia, *{name}*! 🎉 Me alegra mucho. Gracias por confiar en nosotros para encontrar tu próximo hogar. ¡Cualquier duda adicional, aquí estaré! 🏠✨"

    # 4. Requisitos
    if any(k in msg for k in ['requisito', 'papeles', 'que piden']):
        if 'estudio' in msg or 'aparta' in msg:
            return f"*{name}*, para *Apartaestudios*:\n✅ Cédula\n✅ Depósito de $150.000\n✅ Contrato a 6 o 12 meses."
        return f"*{name}*, para *Apartamentos*:\n✅ Cédula\n✅ Carta Laboral\n✅ Extractos (3 meses)\n✅ Codeudor con ingresos dobles."

    # 5. Intervención humana
    if any(k in msg for k in ['asesor', 'persona', 'humano', 'visita', 'cita', 'contacte']):
        link = f"https://wa.me/{OWNER_NUMBER}?text=Hola,%20soy%20{name}%20y%20quiero%20más%20información."
        return f"¡Entendido, *{name}*! 📱 Haz clic aquí para hablar con un asesor y coordinar todo:\n👉 {link}"

    # 6. Selección por número de lista
    if msg.isdigit() and session["results"] and int(msg) <= len(session["results"]):
        return format_property_response(session["results"][int(msg)-1], name)

    # 7. Búsqueda y Filtrados
    props = filter_properties(msg)
    if props:
        session["results"] = props
        return format_property_list(props, name)

    results = search_properties(msg)
    if results:
        return format_property_response(results[0], name)

    return f"*{name}*, cuéntame qué buscas o escribe *'asesor'* para hablar con una persona. 🏠"
