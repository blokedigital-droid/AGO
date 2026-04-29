from sheets_service import filter_properties, format_property_list, search_properties, format_property_response
from whatsapp_service import send_media_message

SALUDO_INICIAL = "¡Hola! Soy *AGO*, te voy a ayudar a encontrar tu próximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar? 😊"
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
        return f"¡Un placer, *{session['name']}*! 🤝 ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Ver todo en Cali*\n4. *Ver todo en Jamundí*"

    name = session["name"]

    # Lógica de Requisitos Diferenciados
    if any(k in msg for k in ['requisito', 'papeles', 'que piden']):
        if 'apartaestudio' in msg:
            return f"*{name}*, los requisitos para *Apartaestudios* son más ágiles:\n✅ Cédula\n✅ Depósito de $150.000\n✅ Contrato a 6 o 12 meses."
        else:
            return f"*{name}*, para *Apartamentos* requerimos:\n✅ Cédula\n✅ Carta Laboral\n✅ Extractos (3 meses)\n✅ Codeudor con ingresos del doble del canon."

    # Si elige por número de lista
    if msg.isdigit() and session["results"] and int(msg) <= len(session["results"]):
        prop = session["results"][int(msg)-1]
        return format_property_response(prop, name)

    # Filtrado por categorías
    props = filter_properties(msg)
    if props:
        session["results"] = props
        return format_property_list(props, name)

    # Búsqueda general
    results = search_properties(msg)
    if results:
        # Intentar enviar imagen si es link directo
        img_url = results[0].get('Link_Fotos','')
        if img_url.endswith(('.jpg', '.png', '.jpeg')):
            send_media_message(phone_number, img_url, "image")
        return format_property_response(results[0], name)

    return f"*{name}*, cuéntame más detalles o escribe *'asesor'* para hablar con una persona. 🏠"
