import sqlite3, json
from sheets_service import search_properties, format_property_response, format_property_list, filter_properties

DB_PATH = "/tmp/ago_memory.db"
OWNER_NUMBER = "573024929820"

def get_user(phone):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, state TEXT, last_results TEXT, last_property TEXT)")
    cursor.execute("SELECT name, state, last_results, last_property FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    if row: return {"name": row[0], "state": row[1], "last_results": json.loads(row[2]) if row[2] else [], "last_property": row[3]}
    return {"name": None, "state": "new", "last_results": [], "last_property": None}

def update_user(phone, name=None, state=None, last_results=None, last_property=None):
    user = get_user(phone)
    n, s, p = (name or user["name"]), (state or user["state"]), (last_property or user["last_property"])
    r = json.dumps(last_results) if last_results is not None else json.dumps(user["last_results"])
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO users (phone, name, state, last_results, last_property) VALUES (?, ?, ?, ?, ?)", (phone, n, s, r, p))
    conn.commit()
    conn.close()

def process_message(phone, message):
    user = get_user(phone)
    msg = message.lower().strip()
    
    # 1. Saludo Inicial
    if user["state"] == "new":
        update_user(phone, state="awaiting_name")
        return "Hola! soy *AGO*, te voy a ayudar a encontrar tu proximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar? 😊"

    if user["state"] == "awaiting_name":
        name = message.strip().title()
        update_user(phone, name=name, state="ready")
        return f"¡Un placer, *{name}*! 🤝 ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Opciones en Cali*\n4. *Opciones en Jamundí*"

    name = user["name"]

    # 2. DESPEDIDA CORRECTA (Sin preguntas adicionales)
    exit_keywords = ['gracias', 'ya agende', 'ya agendé', 'listo', 'chau', 'adiós', 'adios', 'muy amable', 'ya encontré']
    if any(k in msg for k in exit_keywords) and len(msg.split()) <= 5:
        return f"¡Con todo el gusto, *{name}*! 😊 Me alegra haber podido ayudarte hoy. Si ya agendaste, ¡estaremos listos para recibirte! ¡Que tengas un excelente día! 🏠✨"

    # 3. REDIRECCIÓN A ASESOR (Con resumen del inmueble)
    if any(k in msg for k in ['asesor', 'persona', 'humano', 'hablar']):
        text = f"Hola, soy {name} y quiero hablar con un asesor."
        if user["last_property"]:
            text = f"Hola, soy {name}. Estoy interesado en el inmueble *{user['last_property']}* y quiero más información."
        
        link = f"https://wa.me/{OWNER_NUMBER}?text={text.replace(' ', '%20')}"
        return f"¡Claro que sí, *{name}*! 📱 He preparado un resumen de tu interés para el asesor comercial. Haz clic aquí para hablar directamente con él:\n👉 {link}"

    # 4. Lógica de Selección de Menú
    if msg.isdigit():
        val = int(msg)
        if user["last_results"] and 1 <= val <= len(user["last_results"]):
            selected = user["last_results"][val-1]
            update_user(phone, last_results=[], last_property=selected.get('ID')) # GUARDAMOS EL ÚLTIMO VISTO
            return format_property_response(selected, name)
        
        if val == 1: msg = "apartamento"
        elif val == 2: msg = "apartaestudio"
        elif val == 3: msg = "cali"
        elif val == 4: msg = "jamundi"

    # 5. Búsqueda y Filtrado
    results = filter_properties(msg) if len(msg.split()) < 3 else []
    if not results: results = search_properties(msg)

    if len(results) == 1:
        update_user(phone, last_results=[], last_property=results[0].get('ID'))
        return format_property_response(results[0], name)
    elif len(results) > 1:
        update_user(phone, last_results=results)
        return format_property_list(results, name, "que coinciden")

    return f"*{name}*, no logré encontrar algo exacto con eso. 🔍 ¿Buscas apartamentos o apartaestudios? 🏠"
