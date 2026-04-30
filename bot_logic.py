import sqlite3, json
from sheets_service import search_properties, format_property_response, format_property_list, filter_properties

DB_PATH = "/tmp/ago_memory.db"
OWNER_NUMBER = "573024929820"

def get_user(phone):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Añadimos la columna last_type_desc para guardar la descripción completa
    cursor.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, state TEXT, last_results TEXT, last_property TEXT, last_type_desc TEXT)")
    cursor.execute("SELECT name, state, last_results, last_property, last_type_desc FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    if row: return {"name": row[0], "state": row[1], "last_results": json.loads(row[2]) if row[2] else [], "last_property": row[3], "last_type_desc": row[4]}
    return {"name": None, "state": "new", "last_results": [], "last_property": None, "last_type_desc": None}

def update_user(phone, **kwargs):
    user = get_user(phone)
    for key, value in kwargs.items(): user[key] = value
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO users (phone, name, state, last_results, last_property, last_type_desc) VALUES (?, ?, ?, ?, ?, ?)", 
                 (phone, user["name"], user["state"], json.dumps(user["last_results"]), user["last_property"], user["last_type_desc"]))
    conn.commit()
    conn.close()

def process_message(phone, message):
    user = get_user(phone)
    msg = message.lower().strip()
    
    if user["state"] == "new":
        update_user(phone, state="awaiting_name")
        return "Hola! soy *AGO*, te voy a ayudar a encontrar tu proximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar? 😊"

    if user["state"] == "awaiting_name":
        name = message.strip().title()
        update_user(phone, name=name, state="ready")
        return f"¡Un placer, *{name}*! 🤝 ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Opciones en Cali*\n4. *Opciones en Jamundí*"

    name = user["name"]

    # --- LÓGICA DE REQUISITOS ---
    if any(k in msg for k in ['requisito', 'papeles', 'necesito', 'documento']):
        is_apartaestudio = "aparta" in (user["last_type_desc"] or "").lower() or "aparta" in msg
        if is_apartaestudio:
            papeleo = f"✅ *Requisitos para Apartaestudios:*\n- Fotocopia de Cédula.\n- Depósito de $150.000.\n- Contrato flexible."
        else:
            papeleo = f"✅ *Requisitos para Apartamentos:*\n- Fotocopia de Cédula.\n- Carta Laboral y Extractos (3 meses).\n- Codeudor con ingresos dobles."
        msg2 = f"📄 *¡Aplica ahora mismo!*\n\nRealiza el estudio con **El Libertador** aquí:\n👉 https://www.ellibertador.co/\n\n🏢 *Datos:* AGO-2026 | Grupo Inmobiliario S.A.S"
        return [papeleo, msg2]

    # --- REDIRECCIÓN AL ASESOR (DESCRIPTIVA) ---
    if any(k in msg for k in ['asesor', 'persona', 'humano', 'hablar']):
        # Usamos la descripción del inmueble (Tipo) si está disponible
        desc_inmueble = user["last_type_desc"] or "un inmueble de interés"
        text = f"Hola, soy {name}. Estoy interesado en {desc_inmueble} y quiero hablar con un asesor."
        link = f"https://wa.me/{OWNER_NUMBER}?text={text.replace(' ', '%20')}"
        return f"¡Claro, *{name}*! 📱 He preparado un resumen para el asesor. Haz clic aquí para hablar directamente con él:\n👉 {link}"

    # --- BÚSQUEDA Y MENÚS ---
    if msg.isdigit():
        val = int(msg)
        if user["last_results"] and 1 <= val <= len(user["last_results"]):
            selected = user["last_results"][val-1]
            update_user(phone, last_results=[], last_property=selected.get('ID'), last_type_desc=selected.get('Tipo'))
            return format_property_response(selected, name)
        if val == 1: msg = "apartamento"
        elif val == 2: msg = "apartaestudio"
        elif val == 3: msg = "cali"
        elif val == 4: msg = "jamundi"

    results = filter_properties(msg) if len(msg.split()) < 3 else []
    if not results: results = search_properties(msg)

    if len(results) == 1:
        update_user(phone, last_results=[], last_property=results[0].get('ID'), last_type_desc=results[0].get('Tipo'))
        return format_property_response(results[0], name)
    elif len(results) > 1:
        update_user(phone, last_results=results)
        return format_property_list(results, name, "que coinciden")

    if any(k in msg for k in ['gracias', 'ya agende', 'listo', 'adiós']):
        return f"¡Con todo el gusto, *{name}*! 😊 ¡Feliz día! 🏠✨"

    return f"*{name}*, no logré encontrar algo exacto. ¿Buscas apartamentos o apartaestudios? 🏠"
