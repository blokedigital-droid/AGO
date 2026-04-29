from sheets_service import search_properties, format_property_response, format_property_list

SALUDO_INICIAL = "Hola! soy *AGO*, te voy a ayudar a encontrar tu proximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar? 😊"
OWNER_NUMBER = "573024929820"
client_sessions = {}

def process_message(phone_number, message):
    session = client_sessions.setdefault(phone_number, {"name": None, "state": "new", "results": [], "pending_query": None})
    msg = message.lower().strip()
    
    if session["state"] == "new":
        if len(msg.split()) > 1 or any(k in msg for k in ['apto', 'cali', 'jamundi', 'precio', 'donde']):
            session["pending_query"] = msg
        session["state"] = "awaiting_name"
        return SALUDO_INICIAL

    if session["state"] == "awaiting_name":
        session["name"] = message.strip().title()
        session["state"] = "ready"
        name = session["name"]
        welcome = f"¡Un placer, *{name}*! 🤝"
        
        if session["pending_query"]:
            query = session["pending_query"]
            session["pending_query"] = None
            results = search_properties(query)
            if len(results) == 1:
                return f"{welcome} Sobre lo que preguntabas:\n\n" + format_property_response(results[0], name)
            elif len(results) > 1:
                session["results"] = results
                return welcome + " " + format_property_list(results, name, "que coinciden")

        return f"{welcome} ¿Qué tipo de hogar buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Opciones en Cali*\n4. *Opciones en Jamundí*"

    name = session["name"]

    # Selección por número de lista (Prioridad)
    if msg.isdigit() and session["results"] and int(msg) <= len(session["results"]):
        selected = session["results"][int(msg)-1]
        session["results"] = [] # Limpiamos la lista tras elegir
        return format_property_response(selected, name)

    # Intenciones de Cierre o Ayuda
    if any(k in msg for k in ['ya agende', 'ya agendé', 'cita lista']):
        return f"¡Excelente noticia, *{name}*! 🎉 Me alegra mucho. ¡Cualquier duda adicional, aquí estaré! 🏠✨"

    if any(k in msg for k in ['asesor', 'persona', 'humano', 'hablar']):
        link = f"https://wa.me/{OWNER_NUMBER}?text=Hola,%20soy%20{name}%20y%20quiero%20más%20información."
        return f"¡Claro, *{name}*! 📱 Haz clic aquí para hablar con un asesor humano:\n👉 {link}"

    # Búsqueda General
    results = search_properties(msg)
    if len(results) == 1:
        return format_property_response(results[0], name)
    elif len(results) > 1:
        session["results"] = results
        return format_property_list(results, name, "en esa zona")

    return f"*{name}*, no encontré algo exacto. ¿Te gustaría ver todos los *disponibles* o hablar con un *asesor*? 🏠"
