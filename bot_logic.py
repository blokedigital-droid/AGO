import sqlite3, json
from sheets_service import search_properties, format_property_response, format_property_list, filter_properties

DB_PATH = "/tmp/ago_memory.db" # Cambiamos a carpeta temporal de Railway
OWNER_NUMBER = "573024929820"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, state TEXT, last_results TEXT)")
    conn.commit()
    conn.close()

init_db()

def get_user(phone):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, state, last_results FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    if row: return {"name": row[0], "state": row[1], "last_results": json.loads(row[2]) if row[2] else []}
    return {"name": None, "state": "new", "last_results": []}

def update_user(phone, name=None, state=None, last_results=None):
    user = get_user(phone)
    n, s = (name or user["name"]), (state or user["state"])
    r = json.dumps(last_results) if last_results is not None else json.dumps(user["last_results"])
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO users (phone, name, state, last_results) VALUES (?, ?, ?, ?)", (phone, n, s, r))
    conn.commit()
    conn.close()

def process_message(phone, message):
    user = get_user(phone)
    msg = message.lower().strip()
    
    if user["state"] == "new":
        update_user(phone, state="awaiting_name")
        return "¡Hola! Soy *AGO*, te voy a ayudar a encontrar tu próximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar? 😊"

    if user["state"] == "awaiting_name":
        name = message.strip().title()
        update_user(phone, name=name, state="ready")
        return f"¡Un placer, *{name}*! 🤝 ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Opciones en Cali*\n4. *Opciones en Jamundí*"

    name = user["name"]

    if msg.isdigit():
        val = int(msg)
        if user["last_results"] and 1 <= val <= len(user["last_results"]):
            selected = user["last_results"][val-1]
            update_user(phone, last_results=[])
            return format_property_response(selected, name)
        
        if val == 1: msg = "apartamento"
        elif val == 2: msg = "apartaestudio"
        elif val == 3: msg = "cali"
        elif val == 4: msg = "jamundi"

    if any(k in msg for k in ['asesor', 'persona', 'humano', 'hablar']):
        link = f"https://wa.me/{OWNER_NUMBER}?text=Hola,%20soy%20{name}%20y%20quiero%20más%20información."
        return f"¡Entendido, *{name}*! 📱 Haz clic aquí para hablar con un asesor:\n👉 {link}"

    results = filter_properties(msg) if len(msg.split()) < 3 else []
    if not results: results = search_properties(msg)

    if len(results) == 1:
        update_user(phone, last_results=[])
        return format_property_response(results[0], name)
    elif len(results) > 1:
        update_user(phone, last_results=results)
        return format_property_list(results, name, "que coinciden")

    return f"*{name}*, no logré encontrar algo exacto. ¿Buscas apartamentos o apartaestudios? 🏠"
