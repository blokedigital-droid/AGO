import sqlite3, json
from sheets_service import search_properties, format_property_response, format_property_list

DB_PATH = "ago_memory.db"
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
    if row:
        return {"name": row[0], "state": row[1], "last_results": json.loads(row[2]) if row[2] else []}
    return {"name": None, "state": "new", "last_results": []}

def update_user(phone, name=None, state=None, last_results=None):
    user = get_user(phone)
    n = name if name else user["name"]
    s = state if state else user["state"]
    r = json.dumps(last_results) if last_results is not None else json.dumps(user["last_results"])
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO users (phone, name, state, last_results) VALUES (?, ?, ?, ?)", (phone, n, s, r))
    conn.commit()
    conn.close()

def process_message(phone, message):
    user = get_user(phone)
    msg = message.lower().strip()
    
    # 1. Saludo inicial
    if user["state"] == "new":
        update_user(phone, state="awaiting_name")
        return "Hola! soy *AGO*, te voy a ayudar a encontrar tu proximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar? 😊"

    # 2. Captura de nombre
    if user["state"] == "awaiting_name":
        name = message.strip().title()
        update_user(phone, name=name, state="ready")
        return f"¡Un placer, *{name}*! 🤝 ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Opciones en Cali*\n4. *Opciones en Jamundí*"

    name = user["name"]

    # 3. SI EL MENSAJE ES UN NÚMERO (Selección de lista)
    if msg.isdigit() and user["last_results"]:
        idx = int(msg) - 1
        if 0 <= idx < len(user["last_results"]):
            selected = user["last_results"][idx]
            update_user(phone, last_results=[]) # Limpiamos la memoria tras elegir
            return format_property_response(selected, name)

    # 4. Intenciones Humanas
    if any(k in msg for k in ['asesor', 'persona', 'humano', 'visita', 'cita']):
        link = f"https://wa.me/{OWNER_NUMBER}?text=Hola,%20soy%20{name}%20y%20quiero%20más%20información."
        return f"¡Entendido, *{name}*! 📱 Haz clic aquí para hablar con un asesor humano:\n👉 {link}"

    # 5. Búsqueda General
    results = search_properties(msg)
    if len(results) == 1:
        update_user(phone, last_results=[])
        return format_property_response(results[0], name)
    elif len(results) > 1:
        update_user(phone, last_results=results) # GUARDAMOS LOS RESULTADOS
        return format_property_list(results, name, "que encontré")

    return f"*{name}*, no logré encontrar algo exacto. ¿Te gustaría ver los *disponibles* o hablar con un *asesor*? 🏠"
